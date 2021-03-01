// Define some constants that should make it easier to move
// functions across modules
export const MODULE_NAME = 'accounts';

// As projects and invited projects share the exact same functionality but with
// different endpoints, I need to have a way to replicate the functionality without
// duplicating code
export const PROJECT_URL = 'URL';
export const PROJECT_CURRENT_NAME = 'project';

// INVITED PROJECTS
const URL = '/api/v1/user/me/received_invitations';
const CURRENT_NAME = 'invitedproject';
