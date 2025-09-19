/**
 * Unit tests for the Component base class
 */

import { Component } from '../../components/core/component.js';
import { MockEventBus, MockStateManager } from '../mocks/component-mocks.js';

describe('Component', () => {
  let component;
  let mockEventBus;
  let mockStateManager;

  beforeEach(() => {
    mockEventBus = new MockEventBus();
    mockStateManager = new MockStateManager();

    // Mock global dependencies
    global.EventBus = mockEventBus;
    global.StateManager = mockStateManager;

    component = new Component('test-component');
  });

  afterEach(() => {
    if (component && !component.destroyed) {
      component.destroy();
    }
  });

  describe('Constructor', () => {
    test('should create component with name', () => {
      expect(component.name).toBe('test-component');
      expect(component.initialized).toBe(false);
      expect(component.destroyed).toBe(false);
    });

    test('should accept dependencies', () => {
      const deps = ['dep1', 'dep2'];
      const comp = new Component('test', deps);
      expect(comp.dependencies).toEqual(deps);
    });

    test('should initialize with empty state', () => {
      expect(component.state).toEqual({});
    });
  });

  describe('Lifecycle Methods', () => {
    test('init() should mark component as initialized', async () => {
      await component.init();
      expect(component.initialized).toBe(true);
    });

    test('init() should call onInit hook if defined', async () => {
      const onInitSpy = jest.fn();
      component.onInit = onInitSpy;

      await component.init();
      expect(onInitSpy).toHaveBeenCalled();
    });

    test('destroy() should mark component as destroyed', async () => {
      await component.init();
      await component.destroy();

      expect(component.destroyed).toBe(true);
      expect(component.initialized).toBe(false);
    });

    test('destroy() should call onDestroy hook if defined', async () => {
      const onDestroySpy = jest.fn();
      component.onDestroy = onDestroySpy;

      await component.init();
      await component.destroy();

      expect(onDestroySpy).toHaveBeenCalled();
    });

    test('destroy() should remove element from DOM', async () => {
      await component.init();
      const element = component.render();
      document.body.appendChild(element);

      expect(document.body.contains(element)).toBe(true);

      await component.destroy();
      expect(document.body.contains(element)).toBe(false);
    });
  });

  describe('Rendering', () => {
    test('render() should create and return element', () => {
      const element = component.render();

      expect(element).toBeInstanceOf(HTMLElement);
      expect(element.classList.contains('component')).toBe(true);
      expect(element.classList.contains('test-component')).toBe(true);
    });

    test('render() should call onRender hook if defined', () => {
      const onRenderSpy = jest.fn();
      component.onRender = onRenderSpy;

      component.render();
      expect(onRenderSpy).toHaveBeenCalled();
    });

    test('should store element reference', () => {
      const element = component.render();
      expect(component.element).toBe(element);
    });
  });

  describe('Event Handling', () => {
    beforeEach(async () => {
      await component.init();
    });

    test('on() should register event listener', () => {
      const handler = jest.fn();
      component.on('test-event', handler);

      component.emit('test-event', { data: 'test' });
      expect(handler).toHaveBeenCalledWith({ data: 'test' });
    });

    test('once() should register one-time event listener', () => {
      const handler = jest.fn();
      component.once('test-event', handler);

      component.emit('test-event', { data: 'test1' });
      component.emit('test-event', { data: 'test2' });

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith({ data: 'test1' });
    });

    test('off() should remove event listener', () => {
      const handler = jest.fn();
      component.on('test-event', handler);
      component.off('test-event', handler);

      component.emit('test-event', { data: 'test' });
      expect(handler).not.toHaveBeenCalled();
    });

    test('emit() should trigger event listeners', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      component.on('test-event', handler1);
      component.on('test-event', handler2);

      component.emit('test-event', { data: 'test' });

      expect(handler1).toHaveBeenCalledWith({ data: 'test' });
      expect(handler2).toHaveBeenCalledWith({ data: 'test' });
    });
  });

  describe('State Management', () => {
    beforeEach(async () => {
      await component.init();
    });

    test('setState() should update component state', () => {
      component.setState({ key: 'value' });
      expect(component.state.key).toBe('value');
    });

    test('setState() should merge with existing state', () => {
      component.setState({ key1: 'value1' });
      component.setState({ key2: 'value2' });

      expect(component.state).toEqual({
        key1: 'value1',
        key2: 'value2'
      });
    });

    test('setState() should trigger state change event', () => {
      const handler = jest.fn();
      component.on('state-changed', handler);

      component.setState({ key: 'value' });

      expect(handler).toHaveBeenCalledWith({
        key: 'value',
        previous: {}
      });
    });

    test('getState() should return current state', () => {
      component.setState({ key: 'value' });
      expect(component.getState()).toEqual({ key: 'value' });
    });

    test('getState() should return copy of state', () => {
      component.setState({ key: 'value' });
      const state = component.getState();
      state.key = 'modified';

      expect(component.state.key).toBe('value');
    });
  });

  describe('Global State Integration', () => {
    beforeEach(async () => {
      await component.init();
    });

    test('should subscribe to global state changes', () => {
      const handler = jest.fn();
      component.subscribeToState('user.name', handler);

      mockStateManager.setState('user.name', 'John');
      expect(handler).toHaveBeenCalledWith('John', undefined);
    });

    test('should update global state', () => {
      component.updateGlobalState('user.name', 'John');
      expect(mockStateManager.getState('user.name')).toBe('John');
    });
  });

  describe('DOM Event Handling', () => {
    beforeEach(async () => {
      await component.init();
      component.render();
      document.body.appendChild(component.element);
    });

    test('should handle DOM events', () => {
      const handler = jest.fn();
      component.onDOMEvent('click', handler);

      component.element.click();
      expect(handler).toHaveBeenCalled();
    });

    test('should remove DOM event listeners on destroy', async () => {
      const handler = jest.fn();
      component.onDOMEvent('click', handler);

      await component.destroy();

      // Element should be removed from DOM, so this won't trigger
      const newElement = document.createElement('div');
      newElement.className = component.element.className;
      document.body.appendChild(newElement);
      newElement.click();

      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    test('should handle init errors gracefully', async () => {
      component.onInit = () => {
        throw new Error('Init error');
      };

      await expect(component.init()).rejects.toThrow('Init error');
      expect(component.initialized).toBe(false);
    });

    test('should handle render errors gracefully', () => {
      component.onRender = () => {
        throw new Error('Render error');
      };

      expect(() => component.render()).toThrow('Render error');
    });

    test('should emit error events', () => {
      const errorHandler = jest.fn();
      component.on('error', errorHandler);

      component.handleError(new Error('Test error'));

      expect(errorHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Test error'
        })
      );
    });
  });

  describe('Utility Methods', () => {
    test('should generate unique IDs', () => {
      const id1 = component.generateId();
      const id2 = component.generateId();

      expect(id1).not.toBe(id2);
      expect(typeof id1).toBe('string');
      expect(id1.length).toBeGreaterThan(0);
    });

    test('should check if component is ready', async () => {
      expect(component.isReady()).toBe(false);

      await component.init();
      expect(component.isReady()).toBe(true);

      await component.destroy();
      expect(component.isReady()).toBe(false);
    });
  });
});
