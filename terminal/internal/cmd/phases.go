package cmd

import (
	"context"
	"fmt"
	"io"
	"os"

	"github.com/charmbracelet/crush/internal/event"
	"github.com/charmbracelet/crush/internal/legacylift"
	"github.com/charmbracelet/crush/internal/workspace"
	"github.com/charmbracelet/x/term"
	"github.com/spf13/cobra"
)

func init() {
	rootCmd.Flags().String("from", "", "First phase to run (discover, understand, assess, plan, baseline, modernize, verify)")
	rootCmd.Flags().String("until", "", "Last phase to run")
	rootCmd.Flags().StringP("model", "m", "", "Model to use: 'model' or 'provider/model'. Local Ollama is used automatically when no provider is configured")
	rootCmd.Flags().Bool("plain", false, "Print progress lines instead of the TUI")
	rootCmd.AddCommand(phasesListCmd)
}

var phasesListCmd = &cobra.Command{
	Use:   "phases",
	Short: "List the LegacyLift phases and their artifacts",
	RunE: func(cmd *cobra.Command, _ []string) error {
		all, err := legacylift.Phases()
		if err != nil {
			return err
		}
		for _, p := range all {
			fmt.Fprintf(cmd.OutOrStdout(), "%s  %-10s → %s\n", p.Num, p.ID, p.Artifact())
		}
		return nil
	},
}

// runPhases replaces the chat TUI: it executes the documented LegacyLift
// phases on the current directory without asking the user for prompts.
func runPhases(cmd *cobra.Command) error {
	from, _ := cmd.Flags().GetString("from")
	until, _ := cmd.Flags().GetString("until")
	modelFlag, _ := cmd.Flags().GetString("model")
	plain, _ := cmd.Flags().GetBool("plain")

	root, err := ResolveCwd(cmd)
	if err != nil {
		return err
	}
	all, err := legacylift.Phases()
	if err != nil {
		return err
	}
	phases, err := legacylift.Select(all, from, until)
	if err != nil {
		return err
	}

	// Local AI first: if nothing is configured and Ollama is running,
	// point the project at it.
	localModel, err := legacylift.EnsureLocalAI(root, modelFlag)
	if err != nil {
		return err
	}
	if localModel != "" && modelFlag == "" {
		modelFlag = "ollama/" + localModel
	}

	// Every phase is unattended: never stop to ask for permissions.
	if c, _ := cmd.Flags().GetCount("yolo"); c == 0 {
		_ = cmd.Flags().Set("yolo", "1")
	}

	ws, cleanup, err := setupLocalWorkspace(cmd)
	if err != nil {
		return err
	}
	defer cleanup()
	event.SetNonInteractive(true)
	event.AppInitialized()

	if !ws.Config().IsConfigured() {
		return fmt.Errorf("no hay IA configurada: inicia Ollama (ollama serve) o configura un proveedor (ANTHROPIC_API_KEY, OPENAI_API_KEY, … o crush.json)")
	}
	app := ws.(*workspace.AppWorkspace).App()

	agent := func(ctx context.Context, prompt string, w io.Writer) error {
		return app.RunNonInteractive(ctx, w, prompt, modelFlag, "", "", true, "", false)
	}
	runner := &legacylift.Runner{Root: root, Phases: phases, Agent: agent}

	modelName := modelFlag
	if modelName == "" {
		if m := ws.Config().Models; m != nil {
			if large, ok := m["large"]; ok {
				modelName = large.Provider + "/" + large.Model
			}
		}
	}

	if plain || !term.IsTerminal(os.Stdout.Fd()) {
		return legacylift.RunPlain(cmd.Context(), runner, func(s string) { fmt.Fprintln(cmd.OutOrStdout(), s) })
	}
	restoreStderr, _ := detachStderr()
	defer restoreStderr()
	return legacylift.RunTUI(cmd.Context(), runner, modelName)
}
