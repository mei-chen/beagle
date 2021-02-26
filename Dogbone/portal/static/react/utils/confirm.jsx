/**
 * https://jsfiddle.net/fernandokokocha/p9gqqgp7/
 */

import React from 'react';
import { render, unmountComponentAtNode } from 'react-dom';
import $ from 'jquery';

require('./styles/confirm.scss');

const Modal = React.createClass({
  displayName: 'Modal',
  backdrop: function() {
    return <div className='modal-backdrop in' />;
  },

  modal: function() {
    var style = {display: 'block'};
    return (
      <div
        className='modal in'
        tabIndex='-1'
        role='dialog'
        aria-hidden='false'
        ref='modal'
        style={style}
      >
        <div className='modal-dialog'>
          <div className='modal-content'>
            {this.props.children}
          </div>
        </div>
      </div>
    );
  },

  render: function() {
    return (
      <div>
        {this.backdrop()}
        {this.modal()}
      </div>
    );
  }
});

var Confirm = React.createClass({
  displayName: 'Confirm',
  getDefaultProps: function() {
    return {
      confirmLabel: 'OK',
      abortLabel: 'Cancel'
    };
  },

  abort: function() {
    return this.promise.reject();
  },

  confirm: function() {
    return this.promise.resolve();
  },

  componentDidMount: function() {
    this.promise = new $.Deferred();
  },

  render: function() {
    return (
      <Modal>
        <div className='modal-header'>
          <h4 className='modal-title'>
            {this.props.title}
          </h4>
        </div>
        <div className='modal-body'>
          {this.props.message}
        </div>
        <div className='modal-footer'>
          <div className='text-right'>
            <button
              role='abort'
              type='button'
              className='btn btn-default'
              onClick={this.abort}
            >
              {this.props.abortLabel}
            </button>
            {' '}
            <button
              role='confirm'
              type='button'
              className='btn btn-primary'
              ref='confirm'
              onClick={this.confirm}
            >
              {this.props.confirmLabel}
            </button>
          </div>
        </div>
      </Modal>
    );
  }
});

var confirm = function(message, title, options) {
  var cleanup, component, props, wrapper;
  if (title == null) {
    title = "Confirmation";
  }
  if (options == null) {
    options = {};
  }
  props = $.extend({
    title: title,
    message: message
  }, options);
  wrapper = document.body.appendChild(document.createElement('div'));
  component = render(<Confirm {...props}/>, wrapper);
  cleanup = function() {
    unmountComponentAtNode(wrapper);
    return setTimeout(function() {
      return wrapper.remove();
    });
  };
  return component.promise.always(cleanup).promise();
};

module.exports = confirm;
