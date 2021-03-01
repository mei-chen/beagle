import PropTypes from "prop-types";

export const batchPropType = PropTypes.shape({
  id: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  format: PropTypes.string,
  owner_username: PropTypes.string,
  description: PropTypes.string,
  create_date: PropTypes.string.isRequired
});
