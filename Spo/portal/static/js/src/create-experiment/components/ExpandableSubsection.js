import React, { Component, PropTypes } from 'react';
import { ControlLabel, FormGroup, FormControl, Button } from 'react-bootstrap';

class ExpandableSubsection extends Component {
    constructor(props) {
        super(props)
        this._toggleDropdown = this._toggleDropdown.bind(this);
        this.state = {
            isOpen: false
        }
    }

    _toggleDropdown() {
        this.setState({ isOpen: !this.state.isOpen });
    }

    render() {
        const { isOpen } = this.state;
        const { iconClass, title, children } = this.props;
        const iconClassName = iconClass || 'fa fa-rocket';

        return (
            <div className="expandable">
                <span
                    className="expandable-toggle"
                    onClick={this._toggleDropdown}>
                    <i className={iconClassName} />
                    <span className="expandable-toggle-value">{title}</span>
                    { isOpen ? <i className="fa fa-chevron-up" /> : <i className="fa fa-chevron-down" /> }
                </span>

                { isOpen && (
                    <div className="expandable-drop clearfix">{ children }</div>
                )}
            </div>
        )
    }
}

ExpandableSubsection.propTypes = {
    title: PropTypes.string.isRequired,
    iconClass: PropTypes.string,
    children: PropTypes.object.isRequired
}

export default ExpandableSubsection;
