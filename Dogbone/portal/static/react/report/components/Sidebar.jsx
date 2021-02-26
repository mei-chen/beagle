import React from 'react';
import Tooltip from 'react-bootstrap/lib/Tooltip';
import { Link } from 'react-router';
import invariant from 'invariant';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';

require('./styles/Sidebar.scss');


var NavButton = React.createClass({

  propTypes: {
    to: React.PropTypes.string, // react-router Link `to`
    href: React.PropTypes.string, // or supply an `href`
    name: React.PropTypes.string.isRequired, // tooltip name
    description: React.PropTypes.string, // tooltip extended text
    attributes: React.PropTypes.object, //key-value attributes to add to HTML element
  },

  render() {
    const { to, href, name, children, description } = this.props;

    let tooltip = (
      <Tooltip placement="right" id={name}>
        <strong>{name}</strong>
        {description ? [<br key="b"/>, <span key="s">{description}</span>] : null}
      </Tooltip>
    );

    let link;
    if (to) { // this is a react-router Link
      link = <Link {...this.props.attributes} to={to}>{children}</Link>;
    } else if (href) {
      link = <a {...this.props.attributes} href={href}>{children}</a>;
    } else {
      invariant(false, 'neither a `to` nor an `href` were provided to NavButton');
    }

    return (
      <OverlayTrigger overlay={tooltip}>
        {link}
      </OverlayTrigger>
    );
  }

});

var Sidebar = React.createClass({

  render() {
    return (
      <aside className="beagle-sidebar">
        <nav>
          <NavButton
            attributes={{ 'id' : 'step1' }}
            to="widget-panel"
            name="Widget Panel"
            description="A high level infographic view of the agreement."
          >
            <i className="fa fa-tachometer-alt"/>
          </NavButton>
          <NavButton to="detail-view" name="Detail View"
            description="See the full text of your agreement with Beagle's annotations."
          >
            <i className="fa fa-file-alt"/>
          </NavButton>
          <NavButton to="clause-table" name="Clause Table"
            description="View annotated clauses in tabular format and export to CSV."
          >
            <i className="fa fa-list-alt"/>
          </NavButton>
          <NavButton to="context-view" name="Context View"
            description="See where annotated clauses appear in the text of the agreement."
          >
            <i className="fa fa-columns"/>
          </NavButton>
        </nav>
      </aside>
    );
  }

});


module.exports = Sidebar;
