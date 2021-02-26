import React from 'react';
import ReactDOM from 'react-dom';

require('./styles/ZipPassword.scss');

const ZipPassword = React.createClass({
  propTypes: {
    showZipPassword: React.PropTypes.bool,
    submitZipPassword: React.PropTypes.func,
    cancel: React.PropTypes.func,
    wrongPassword: React.PropTypes.bool,
    encryptedDocuments: React.PropTypes.array
  },

  defaultProps: {
    wrongPassword: false,
    encryptedDocuments: []
  },

  getInitialState() {
    return {
      isSubmited: false
    }
  },

  componentWillReceiveProps(nextProps) {
    nextProps.wrongPassword ? this.setState({ isSubmited: false }) : null;
  },

  handleSubmit() {
    const answer = [];
    this.setState({
      isSubmited: true
    })
    this.props.encryptedDocuments.map((value) => {
      let input = ReactDOM.findDOMNode(this.refs[value.name]);
      answer.push({
        name: value.name,
        path: value.path,
        password: input.value
      })
    })
    this.props.submitZipPassword(answer);
  },
  render() {
    const { encryptedDocuments } = this.props;
    var inputs;
    if (encryptedDocuments) {
      inputs = encryptedDocuments.map((value, key) => {
        return (
          <div key={key}>
            <label htmlFor={value.name}>
              <i className="fa fa-file-archive"/>
              {value.name}:
            </label>
            <input
              required
              autoComplete="off"
              ref={value.name}
              name={value.name}
              type="password"
              placeholder="Password"
              className="password-input"
            />
          </div>
        )
      })
    }
    return (
      <div className="zip-password-form">
        <h2 className="zip-password-header">Unlock zip archive</h2>
        {inputs}
        {this.props.wrongPassword ? <span className="wrong-password">Wrong password please try again</span> : null }
        {this.state.isSubmited ? <div className="btn disabled">Verification</div> : <div className="btn" onClick={this.handleSubmit}>Submit</div>}
        <div className="cancel" onClick={this.props.cancel}>Cancel</div>
      </div>
    )
  }
})


module.exports = ZipPassword;
