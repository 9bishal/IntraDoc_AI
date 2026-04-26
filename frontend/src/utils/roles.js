export const ROLE = {
  ADMINISTRATOR: 'administrator',
  HR: 'hr',
  FINANCE: 'finance',
  LEGAL: 'legal',
};

export const roleToDepartments = {
  [ROLE.ADMINISTRATOR]: ['hr', 'finance', 'legal', 'graph'],
  [ROLE.HR]: ['hr'],
  [ROLE.FINANCE]: ['finance'],
  [ROLE.LEGAL]: ['legal'],
};

export const normalizeRole = (rawRole) => {
  const role = (rawRole || '').toString().trim().toLowerCase();

  if (['admin', 'administrator'].includes(role)) return ROLE.ADMINISTRATOR;
  if (role === 'accounts') return ROLE.FINANCE;
  if (role in roleToDepartments) return role;

  return ROLE.HR;
};

export const getAccessibleDepartments = (role) => {
  const normalized = normalizeRole(role);
  return roleToDepartments[normalized] || [];
};

export const canAccessDepartment = (role, department) => {
  const normalizedDept = (department || '').toLowerCase();
  return getAccessibleDepartments(role).includes(normalizedDept);
};
