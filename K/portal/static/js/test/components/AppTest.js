import React from 'react';
import expect from 'chai';
import { shallow, mount } from 'enzyme';
import { ContentComponent } from '../../src/LocalFolder/components/ContentComponent';
import { PickerPanel } from '../../src/LocalFolder/components/PickerPanel';
import { ListOfBatches } from '../../src/base/components/ListOfBatches';

describe('<ContentComponent />', function () {

  beforeEach(function () {
    this.component = shallow(<ContentComponent />);
  });

  it('Component should be defined', function () {
    it('renders <ContentComponent /> component', () => {
      const wrapper = shallow(<ContentComponent />);
      expect(wrapper).toExist();
    });
  });

  it('Component should be React.Class type', function () {
    it('renders <ContentComponent /> component', function () {
      const wrapper = shallow(<ContentComponent />);
      expect(wrapper).isCompositeComponentWithType();
    });
  });

  it('It should have div with className wrapper', function () {
    it('renders <ContentComponent /> component', function () {
      const wrapper = shallow(<ContentComponent />);
      expect(wrapper.find('.wrapper')).to.have.length(1);
    });
  });

  it('Contains an <PickerPanel /> component', function () {
    it('renders <PickerPanel /> component', function () {
      const wrapper = mount(<ContentComponent />);
      expect(wrapper.find(PickerPanel)).to.have.length(1);
    });
  });

  it('Contains an <ListOfBatches /> component', function () {
    it('renders <ListOfBatches /> component', function () {
      const wrapper = mount(<ContentComponent />);
      expect(wrapper.find(ListOfBatches)).to.have.length(1);
    });
  });
});
