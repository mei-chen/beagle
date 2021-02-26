jest.dontMock('../common/components/Header.jsx');

describe('Header', function() {
  it('exists', function() {
    var React = require('react/addons');
    var Header = require('../common/components/Header.jsx');
    var TestUtils = React.addons.TestUtils;

    var headerTree = TestUtils.renderIntoDocument(
      <Header/>
    );

    var headerDOM = TestUtils.findRenderedComponentWithType(
      headerTree, Header
    );
  });
});
