var React = require('react');
var { Link, State } = require('react-router');
var invariant = require('invariant');

require('./styles/Footer.scss');


var NavButton = React.createClass({

  propTypes: {
    to: React.PropTypes.string, // react-router Link `to`
    href: React.PropTypes.string, // or supply an `href`
    name: React.PropTypes.string.isRequired, // tooltip name
    attributes: React.PropTypes.object, //key-value attributes to add to HTML element
  },

  render() {
    let { to, href, name, children } = this.props;

    let link;
    if (to) { // this is a react-router Link
      link = <Link {...this.props.attributes} to={to}>{children}</Link>;
    } else if (href) {
      link = <a {...this.props.attributes} href={href}>{children}</a>;
    } else {
      invariant(false, 'neither a `to` nor an `href` were provided to NavButton');
    }

    return (
      <div className="nav-button">
        {link}
      </div>
    );
  }

});


var Footer = React.createClass({

  mixins: [State],

  propTypes: {
    page: React.PropTypes.string,
  },

  getDefaultProps() {
    return {
      page: "context-view"
    };
  },

  render() {
    var page = this.props.page;

    var btn1to = "clause-table";
    var btn1name = "Search";
    var btn2to = "detail-view";
    var btn2name = "Review";

    switch (page) {
      case "clause-table":
        btn1to = "context-view";
        btn1name = "Back";
        btn2to = "detail-view";
        btn2name = "Review";
        break;
      case "detail-view":
        btn1to = "clause-table";
        btn1name = "Search";
        btn2to = "context-view";
        btn2name = "Back";
        break;
      case "context-view":
        var queryString = this.getQuery();
        if (queryString["idx"]) {
          btn1to = "clause-table";
          btn1name = "Search";
          btn2to = "context-view";
          btn2name = "Back";
        }
        break;
      default:
        break;
    }

    return (
      <div id="footer" className="beagle-footer">
        <nav>
          <NavButton to={btn1to} name={btn1name} >
            {btn1name}
          </NavButton>
          <NavButton to={btn2to} name={btn2name} >
            {btn2name}
          </NavButton>
        </nav>
      </div>
    );
  }

});


module.exports = Footer;
