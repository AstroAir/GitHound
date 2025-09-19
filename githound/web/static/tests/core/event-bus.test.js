/**
 * Unit tests for the EventBus
 */

import { EventBus } from '../../components/core/event-bus.js';

describe('EventBus', () => {
  let eventBus;

  beforeEach(() => {
    eventBus = new EventBus();
  });

  afterEach(() => {
    eventBus.clear();
  });

  describe('Event Registration', () => {
    test('should register event listener', () => {
      const handler = jest.fn();
      eventBus.on('test-event', handler);

      expect(eventBus.listeners.has('test-event')).toBe(true);
      expect(eventBus.listeners.get('test-event')).toContain(
        expect.objectContaining({ handler })
      );
    });

    test('should register multiple listeners for same event', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      eventBus.on('test-event', handler1);
      eventBus.on('test-event', handler2);

      const listeners = eventBus.listeners.get('test-event');
      expect(listeners).toHaveLength(2);
    });

    test('should register one-time listener', () => {
      const handler = jest.fn();
      eventBus.once('test-event', handler);

      const listeners = eventBus.listeners.get('test-event');
      expect(listeners[0].options.once).toBe(true);
    });

    test('should register listener with namespace', () => {
      const handler = jest.fn();
      eventBus.on('test-event.namespace', handler);

      expect(eventBus.listeners.has('test-event.namespace')).toBe(true);
    });

    test('should register listener with priority', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      eventBus.on('test-event', handler1, { priority: 1 });
      eventBus.on('test-event', handler2, { priority: 10 });

      const listeners = eventBus.listeners.get('test-event');
      expect(listeners[0].options.priority).toBe(10);
      expect(listeners[1].options.priority).toBe(1);
    });
  });

  describe('Event Emission', () => {
    test('should emit event to registered listeners', () => {
      const handler = jest.fn();
      eventBus.on('test-event', handler);

      eventBus.emit('test-event', { data: 'test' });

      expect(handler).toHaveBeenCalledWith({ data: 'test' });
    });

    test('should emit event to multiple listeners', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      eventBus.on('test-event', handler1);
      eventBus.on('test-event', handler2);

      eventBus.emit('test-event', { data: 'test' });

      expect(handler1).toHaveBeenCalledWith({ data: 'test' });
      expect(handler2).toHaveBeenCalledWith({ data: 'test' });
    });

    test('should emit event with no data', () => {
      const handler = jest.fn();
      eventBus.on('test-event', handler);

      eventBus.emit('test-event');

      expect(handler).toHaveBeenCalledWith(undefined);
    });

    test('should not emit to non-existent event', () => {
      const handler = jest.fn();
      eventBus.on('other-event', handler);

      eventBus.emit('test-event', { data: 'test' });

      expect(handler).not.toHaveBeenCalled();
    });

    test('should emit events in priority order', () => {
      const callOrder = [];

      const handler1 = () => callOrder.push('handler1');
      const handler2 = () => callOrder.push('handler2');
      const handler3 = () => callOrder.push('handler3');

      eventBus.on('test-event', handler1, { priority: 1 });
      eventBus.on('test-event', handler2, { priority: 10 });
      eventBus.on('test-event', handler3, { priority: 5 });

      eventBus.emit('test-event');

      expect(callOrder).toEqual(['handler2', 'handler3', 'handler1']);
    });
  });

  describe('One-time Listeners', () => {
    test('should remove one-time listener after emission', () => {
      const handler = jest.fn();
      eventBus.once('test-event', handler);

      eventBus.emit('test-event', { data: 'test1' });
      eventBus.emit('test-event', { data: 'test2' });

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith({ data: 'test1' });
    });

    test('should handle multiple one-time listeners', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      eventBus.once('test-event', handler1);
      eventBus.once('test-event', handler2);

      eventBus.emit('test-event', { data: 'test' });

      expect(handler1).toHaveBeenCalledTimes(1);
      expect(handler2).toHaveBeenCalledTimes(1);

      eventBus.emit('test-event', { data: 'test2' });

      expect(handler1).toHaveBeenCalledTimes(1);
      expect(handler2).toHaveBeenCalledTimes(1);
    });
  });

  describe('Event Removal', () => {
    test('should remove specific event listener', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      eventBus.on('test-event', handler1);
      eventBus.on('test-event', handler2);

      eventBus.off('test-event', handler1);
      eventBus.emit('test-event', { data: 'test' });

      expect(handler1).not.toHaveBeenCalled();
      expect(handler2).toHaveBeenCalledWith({ data: 'test' });
    });

    test('should remove all listeners for event', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      eventBus.on('test-event', handler1);
      eventBus.on('test-event', handler2);

      eventBus.off('test-event');
      eventBus.emit('test-event', { data: 'test' });

      expect(handler1).not.toHaveBeenCalled();
      expect(handler2).not.toHaveBeenCalled();
    });

    test('should remove listeners by namespace', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();
      const handler3 = jest.fn();

      eventBus.on('test-event.namespace1', handler1);
      eventBus.on('test-event.namespace2', handler2);
      eventBus.on('other-event.namespace1', handler3);

      eventBus.offNamespace('namespace1');

      eventBus.emit('test-event.namespace1');
      eventBus.emit('test-event.namespace2');
      eventBus.emit('other-event.namespace1');

      expect(handler1).not.toHaveBeenCalled();
      expect(handler2).toHaveBeenCalled();
      expect(handler3).not.toHaveBeenCalled();
    });
  });

  describe('Wildcard Events', () => {
    test('should emit to wildcard listeners', () => {
      const wildcardHandler = jest.fn();
      const specificHandler = jest.fn();

      eventBus.on('*', wildcardHandler);
      eventBus.on('test-event', specificHandler);

      eventBus.emit('test-event', { data: 'test' });

      expect(wildcardHandler).toHaveBeenCalledWith('test-event', { data: 'test' });
      expect(specificHandler).toHaveBeenCalledWith({ data: 'test' });
    });

    test('should support pattern matching', () => {
      const patternHandler = jest.fn();

      eventBus.on('user.*', patternHandler);

      eventBus.emit('user.login', { userId: 1 });
      eventBus.emit('user.logout', { userId: 1 });
      eventBus.emit('system.start', {});

      expect(patternHandler).toHaveBeenCalledTimes(2);
      expect(patternHandler).toHaveBeenCalledWith('user.login', { userId: 1 });
      expect(patternHandler).toHaveBeenCalledWith('user.logout', { userId: 1 });
    });
  });

  describe('Event History', () => {
    test('should track event history', () => {
      eventBus.emit('event1', { data: 'test1' });
      eventBus.emit('event2', { data: 'test2' });

      const history = eventBus.getHistory();

      expect(history).toHaveLength(2);
      expect(history[0]).toMatchObject({
        event: 'event1',
        data: { data: 'test1' }
      });
      expect(history[1]).toMatchObject({
        event: 'event2',
        data: { data: 'test2' }
      });
    });

    test('should limit history size', () => {
      eventBus.maxHistorySize = 2;

      eventBus.emit('event1');
      eventBus.emit('event2');
      eventBus.emit('event3');

      const history = eventBus.getHistory();
      expect(history).toHaveLength(2);
      expect(history[0].event).toBe('event2');
      expect(history[1].event).toBe('event3');
    });

    test('should clear history', () => {
      eventBus.emit('event1');
      eventBus.emit('event2');

      eventBus.clearHistory();

      expect(eventBus.getHistory()).toHaveLength(0);
    });
  });

  describe('Error Handling', () => {
    test('should handle listener errors gracefully', () => {
      const errorHandler = jest.fn();
      const goodHandler = jest.fn();

      eventBus.on('test-event', () => {
        throw new Error('Handler error');
      });
      eventBus.on('test-event', goodHandler);
      eventBus.on('error', errorHandler);

      eventBus.emit('test-event', { data: 'test' });

      expect(goodHandler).toHaveBeenCalledWith({ data: 'test' });
      expect(errorHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Handler error'
        })
      );
    });

    test('should continue processing after error', () => {
      const handler1 = jest.fn(() => {
        throw new Error('Error in handler1');
      });
      const handler2 = jest.fn();
      const handler3 = jest.fn();

      eventBus.on('test-event', handler1);
      eventBus.on('test-event', handler2);
      eventBus.on('test-event', handler3);

      eventBus.emit('test-event');

      expect(handler1).toHaveBeenCalled();
      expect(handler2).toHaveBeenCalled();
      expect(handler3).toHaveBeenCalled();
    });
  });

  describe('Utility Methods', () => {
    test('should check if event has listeners', () => {
      expect(eventBus.hasListeners('test-event')).toBe(false);

      eventBus.on('test-event', jest.fn());
      expect(eventBus.hasListeners('test-event')).toBe(true);
    });

    test('should get listener count', () => {
      expect(eventBus.getListenerCount('test-event')).toBe(0);

      eventBus.on('test-event', jest.fn());
      eventBus.on('test-event', jest.fn());

      expect(eventBus.getListenerCount('test-event')).toBe(2);
    });

    test('should list all events', () => {
      eventBus.on('event1', jest.fn());
      eventBus.on('event2', jest.fn());

      const events = eventBus.getEvents();
      expect(events).toEqual(['event1', 'event2']);
    });

    test('should clear all listeners', () => {
      eventBus.on('event1', jest.fn());
      eventBus.on('event2', jest.fn());

      eventBus.clear();

      expect(eventBus.listeners.size).toBe(0);
      expect(eventBus.getHistory()).toHaveLength(0);
    });
  });
});
