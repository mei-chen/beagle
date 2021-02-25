import React, { Component, PropTypes } from 'react'
import { Alert } from 'react-bootstrap';

class TemporaryMessage extends Component {
    constructor(props) {
        super(props)
        this.state = {
            visible: true
        }
        this.timeoutID = null;
        this.defaultTimeout = 3000;
    }

    componentDidMount() {
        const timeout = this.props.timeout || this.defaultTimeout;
        this.timeoutID = setTimeout(() => this.setState({ visible: false }), timeout);
    }

    componentWillUnmount() {
        clearTimeout(this.timeoutID);
    }

    render() {
        const { visible } = this.state;
        const { children, style } = this.props;
        const bsStyle = style || 'success';

        if(!visible) return null;

        return (
            <Alert bsStyle={bsStyle}>{ children }</Alert>
        )
    }
}

TemporaryMessage.propTypes = {
    children: PropTypes.string.isRequired,
    style: PropTypes.oneOf(['success', 'warning', 'danger']),
    timeout: PropTypes.number
}

export default TemporaryMessage;
