package legacylift

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Agent runs a single prompt non-interactively and streams the answer to w.
// It is provided by the cmd package so this package does not depend on the
// app internals (and stays testable).
type Agent func(ctx context.Context, prompt string, w io.Writer) error

// Status of a phase.
type Status int

const (
	Pending Status = iota
	Running
	Done
	Failed
	Skipped
)

// Event is sent by the runner while it works.
type Event struct {
	Index  int
	Status Status
	Chunk  string // streamed model output
	Err    error
	Took   time.Duration
}

// Runner executes phases in order on Root.
type Runner struct {
	Root   string
	Phases []Phase
	Agent  Agent
}

// skipCopy are top-level entries never copied into the candidate.
var skipCopy = map[string]bool{Dir: true, ".git": true, ".crush": true, "crush.json": true, ".crush.json": true, "node_modules": true}

// prepareCandidate copies the original sources into .legacylift/candidate
// so Modernize never touches the original.
func (r *Runner) prepareCandidate() error {
	dst := filepath.Join(r.Root, Dir, "candidate")
	if err := os.RemoveAll(dst); err != nil {
		return err
	}
	if err := os.MkdirAll(dst, 0o755); err != nil {
		return err
	}
	return filepath.WalkDir(r.Root, func(p string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(r.Root, p)
		if rel == "." {
			return nil
		}
		top := strings.Split(filepath.ToSlash(rel), "/")[0]
		if skipCopy[top] {
			if d.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		target := filepath.Join(dst, rel)
		if d.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		if !d.Type().IsRegular() {
			return nil
		}
		b, err := os.ReadFile(p)
		if err != nil {
			return err
		}
		return os.WriteFile(target, b, 0o644)
	})
}

type chunkWriter struct {
	idx  int
	send func(Event)
	buf  strings.Builder
}

func (c *chunkWriter) Write(p []byte) (int, error) {
	c.buf.Write(p)
	c.send(Event{Index: c.idx, Status: Running, Chunk: string(p)})
	return len(p), nil
}

// Run executes every phase sequentially. It stops at the first failure.
func (r *Runner) Run(ctx context.Context, send func(Event)) error {
	if err := os.MkdirAll(filepath.Join(r.Root, Dir), 0o755); err != nil {
		return err
	}
	prev := "(no hay artefacto previo)"
	for i, ph := range r.Phases {
		if ctx.Err() != nil {
			return ctx.Err()
		}
		if i > 0 {
			prev = r.Phases[i-1].Artifact()
		} else if ph.Num != "01" {
			prev = previousArtifact(ph)
		}
		send(Event{Index: i, Status: Running})
		start := time.Now()

		if ph.ID == "modernize" {
			if err := r.prepareCandidate(); err != nil {
				send(Event{Index: i, Status: Failed, Err: fmt.Errorf("no se pudo copiar la candidata: %w", err)})
				return err
			}
		}

		w := &chunkWriter{idx: i, send: send}
		art := filepath.Join(r.Root, ph.Artifact())
		var err error
		// Small local models sometimes finish without writing anything:
		// retry once with an explicit reminder before failing the phase.
		for attempt := 1; attempt <= 2; attempt++ {
			prompt := ph.Prompt(prev)
			if attempt > 1 {
				prompt += "\n\nIMPORTANTE: el intento anterior no dejó resultado. Escribe ahora el archivo `" +
					ph.Artifact() + "` con la herramienta de escritura, o responde con el contenido completo en Markdown."
				send(Event{Index: i, Status: Running, Chunk: "\n— reintentando la fase —\n"})
			}
			err = r.Agent(ctx, prompt, w)
			if err != nil || hasContent(art) || strings.TrimSpace(w.buf.String()) != "" {
				break
			}
		}
		took := time.Since(start)
		if err != nil {
			send(Event{Index: i, Status: Failed, Err: err, Took: took})
			return err
		}
		// If the model answered but did not write the artifact itself,
		// keep its answer as the artifact so nothing is lost.
		if !hasContent(art) {
			if out := strings.TrimSpace(w.buf.String()); out != "" {
				_ = os.WriteFile(art, []byte("# "+ph.Title+"\n\n"+out+"\n"), 0o644)
			} else {
				err := fmt.Errorf("la fase no produjo %s", ph.Artifact())
				send(Event{Index: i, Status: Failed, Err: err, Took: took})
				return err
			}
		}
		send(Event{Index: i, Status: Done, Took: took})
	}
	return nil
}

func previousArtifact(ph Phase) string {
	all, err := Phases()
	if err != nil {
		return ""
	}
	for i, p := range all {
		if p.ID == ph.ID && i > 0 {
			return all[i-1].Artifact()
		}
	}
	return ""
}

func hasContent(path string) bool {
	st, err := os.Stat(path)
	return err == nil && st.Size() > 0
}
