import PropTypes from "prop-types";

export const projectPropType = PropTypes.shape({
  id: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  status_verbose: PropTypes.string.isRequired,
  owner_username: PropTypes.string,
  // FIXME: next two types change to number after implementation on the backend
  batch_count: PropTypes.string,
  classifier_count: PropTypes.string,
  resource_uri: PropTypes.string.isRequired
});
