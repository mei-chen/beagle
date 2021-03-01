import PropTypes from "prop-types";

export const regexPropType = PropTypes.shape({
  id: PropTypes.number.isRequired,
  content: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
}).isRequired;


export const reportPropType = PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    csv: PropTypes.object.isRequired
}).isRequired;
