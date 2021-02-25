import React from 'react';

const styles = {
  root: {
    fontFamily: '"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
    fontWeight: 300,
    minHeight: '100%',
    paddingBottom: '40px' // footer height
  },
  header: {
    backgroundColor: '#5D101A',
    color: 'white',
    padding: '14px 22px',
    maxHeight: '56px',
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
  style: React.PropTypes.object,
  title: React.PropTypes.oneOfType([
    React.PropTypes.string,
    React.PropTypes.object,
  ]),
  children: React.PropTypes.object,
};

export default MaterialTitlePanel;
