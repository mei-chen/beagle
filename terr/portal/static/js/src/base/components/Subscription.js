import React, { PropTypes } from 'react';
import Timestamp from 'react-time';
import { Popover, OverlayTrigger } from 'react-bootstrap';

const FREE = 'FREE';
const PAID = 'PAID';
const ENTERPRISE = 'ENTERPRISE';

const PLANS = {
  [FREE]:       { privateLimit: 3,  color: '#7f7676', displayName: 'FREE' },
  [PAID]:       { privateLimit: 20, color: '#638142', displayName: 'Dogbone ($20/mo)' },
  [ENTERPRISE]: { privateLimit: -1, color: '#a88a66', displayName: 'Enterprise' },
}

const Subscription = ({ plan, expires, repos }) => {
  const privateOutOf = PLANS[plan].privateLimit === -1 ?
    <span className="subs-unlimited">(unlimited)</span> :
    <span className="subs-out-of">/ { PLANS[plan].privateLimit }</span>;

  const planPopover = (
    <Popover id="plan-popover" title={PLANS[plan].displayName}>
      <ul className="subs-details">
        <li>
          <strong>Public repos: </strong><span>unlimited</span>
        </li>
        <li>
          <strong>Private repos: </strong><span>{ PLANS[plan].privateLimit === -1 ? 'unlimited' : PLANS[plan].privateLimit }</span>
        </li>
      </ul>
    </Popover>
  );

  return (
    <div className={`subs ${plan === FREE ? 'subs--has-advs' : ''}`}>
      {/* content */}
      <div className="subs-content">
        <div className="subs-block">
          <strong>Current subscription: </strong>
          <OverlayTrigger trigger={['hover', 'focus']} placement="right" overlay={planPopover}>
            <strong style={{ color: PLANS[plan].color }}>{ PLANS[plan].displayName }</strong>
          </OverlayTrigger>
        </div>
        { expires && (
          <div className="subs-block">
            <strong>Expires: </strong>
            <span>
              <Timestamp
                value={ expires }
                locale="en"
                format="YYYY/MM/DD" />
            </span>
          </div>
        ) }
        <div className="subs-block">
          <strong>Usage: </strong>
          <ul className="subs-repos">
            <li>
              <strong>Public repos: </strong>
              <span>{ repos.public } <span className="subs-unlimited">(unlimited)</span></span>
            </li>
            <li>
              <strong>Private repos: </strong>
              <span>{ repos.private } { privateOutOf }</span>
            </li>
          </ul>
        </div>
      </div>

      {/* advsertisement */}
      { plan === FREE && (
        <div className="advs">
          <span className="advs-title"><span className="advs-name">Dogbone</span> Subscription</span>
          <ul className="advs-offers">
            <li><span className="advs-offer">Unlimited</span> Public Repositories</li>
            <li><span className="advs-offer">Up to 20</span> Private Repositories</li>
          </ul>
          <div className="advs-bottom">
            <span className="advs-price">$20/mo</span>
            <a className="advs-button" href="/marketing/subscribe">Upgrade</a>
          </div>
        </div>
      )}
    </div>
  )
};

Subscription.propTypes = {
  plan: PropTypes.oneOf([FREE, PAID, ENTERPRISE]),
  expires: PropTypes.string,
  repos: PropTypes.object.isRequired
};

export default Subscription;
