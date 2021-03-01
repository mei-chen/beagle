var React = require('react');
var Reflux = require('reflux');
var Router = require('react-router');
var {
  Link,
  Route,
  RouteHandler,
  DefaultRoute,
  NotFoundRoute,
  Redirect,
  State,
} = Router;
var invariant = require('invariant');

var UserStore = require('common/stores/UserStore');

var Header = require('./components/Header');
var Footer = require('./components/Footer');
var ContextView = require('./components/ContextView');
var ClauseTableView = require('./components/ClauseTableView');
var DetailView = require('./components/DetailView');
var NotFound = require('report/components/NotFound');

require('./components/styles/Main.scss');


var App = React.createClass({

  mixins: [Reflux.connect(UserStore, "user"), State],

  getInitialState() {
    return {
      introObject: null,
    };
  },

  componentDidUpdate(){
    window.Intercom('update');
  },

  getCurrentRouteName() {
    var routes = this.getRoutes();
    invariant(routes.length === 2, "Unexpected routes list");
    if (routes[1].path === "/") {
      return "context-view";
    } else {
      return routes[1].name;
    }
  },

  render() {
    return (
      <div className="app">
        <main>
          <Header ref="Header" shouldShrink />
          <div className="content-wrap">
            <RouteHandler />
          </div>
          <Footer page={this.getCurrentRouteName()} />
        </main>
      </div>
    );
  }

});


var routes = (
    <Route name="app" path="/" handler={App}>
        <Route name="context-view" path="/context-view" handler={ContextView}/>
        <Route name="clause-table" path="/clause-table" handler={ClauseTableView}/>
        <Route name="detail-view" path="/detail-view" handler={DetailView}/>
        <DefaultRoute handler={ContextView}/>
        <NotFoundRoute handler={NotFound}/>
    </Route>
);


Router.run(routes, (Handler) => {
    React.render(<Handler />, document.getElementById("react-app"));
});
