/**
 * userDisplayName
 *
 * Generates a string which is used for identifying a Beagle user where
 * required. Uses the first and last name if available, otherwise it defaults to
 * their email address.
 *
 * @param {object} user
 */
function userDisplayName(user) {
  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`;
  } else {
    return `${user.email}`;
  }
}

module.exports = userDisplayName;
