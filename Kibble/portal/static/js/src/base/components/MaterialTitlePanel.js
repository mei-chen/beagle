import React from 'react';
import PropTypes from 'prop-types';

const styles = {
  root: {
    fontFamily: '"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
    fontWeight: 300,
  },
  header: {
    backgroundColor: '#5D101A',
    color: 'white',
    padding: '16px',
    fontSize: '1.5em',
  },
};

const MaterialTitlePanel = (props) => {
  const rootStyle = props.style ? {...styles.root, ...props.style} : styles.root;

  return (
    <div style={rootStyle}>
      <div style={styles.header}>{props.title}</div>
      {props.children}
    </div>
  );
};

MaterialTitlePanel.propTypes = {
  style: PropTypes.shape({}),
  title: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object,
  ]),
  children: PropTypes.shape({}),
};

export default MaterialTitlePanel;
