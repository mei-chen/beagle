var React = require('react');

require('./styles/Footer.scss');   //stylings for component

var Footer = React.createClass({
  render() {
    const year = new Date().getFullYear();
    return (
      <div className="footer">
        <div className="footer-wrap">
          Copyright &copy; {year} Beagle Inc. All rights reserved.
          <a href="/terms_and_conditions" style={{ marginLeft: '165px' }}>Terms and Conditions</a>
        </div>
      </div>
    );
  }
});

module.exports = Footer;
