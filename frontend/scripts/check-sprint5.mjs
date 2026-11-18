// Structural contracts complement backend integration tests and Angular template compilation.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=(path)=>readFileSync(new URL('../'+path,import.meta.url),'utf8');
const api=read('src/app/core/api/api.service.ts');
const facade=read('src/app/core/state/workspace.facade.ts');
const consoleTs=read('src/app/features/organizations/organization-console/organization-console.component.ts');
const consoleHtml=read('src/app/features/organizations/organization-console/organization-console.component.html');
const auth=read('src/app/features/auth/auth-page/auth-page.component.html');
const create=read('src/app/features/projects/project-dialogs/project-dialogs.component.html');
const bar=read('src/app/features/shell/workspace-topbar/workspace-topbar.component.html');
for (const method of ['organizations()','createOrganization(','organizationMembers(','inviteMember(','acceptInvitation(','updateMemberRole(','removeMember(','organizationReport(','organizationUsage(','organizationAudit(']) {
  assert.ok(api.includes(method), 'API missing '+method);
}
for(const contract of ['get organizations()','set organizations(','loadOrganizations()','get createOrganizationId()','get invitationToken()']) {
  assert.ok(facade.includes(contract),'Facade missing '+contract);
}
assert.match(consoleTs,/selector:\s*'ll-organization-console'/);
assert.match(consoleTs,/templateUrl:\s*'\.\/organization-console\.component\.html'/);
assert.match(consoleTs,/styleUrl:\s*'\.\/organization-console\.component\.css'/);
assert.ok(consoleHtml.includes('report()') && consoleHtml.includes('members()') && consoleHtml.includes('audit()'));
assert.ok(bar.includes('<ll-organization-console/>'));
assert.ok(create.includes('vm.createOrganizationId'));
assert.ok(auth.includes('vm.invitationToken'));
console.log('Sprint 5 frontend structural checks passed');
