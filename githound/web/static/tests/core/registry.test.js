/**
 * Unit tests for the Component Registry
 */

import { ComponentRegistry } from '../../components/core/registry.js';
import { MockComponent } from '../mocks/component-mocks.js';

describe('ComponentRegistry', () => {
  let registry;
  let MockComponentA, MockComponentB, MockComponentC;

  beforeEach(() => {
    registry = new ComponentRegistry();

    // Create mock component classes
    MockComponentA = class extends MockComponent {
      constructor() { super('component-a'); }
    };

    MockComponentB = class extends MockComponent {
      constructor() { super('component-b', ['component-a']); }
    };

    MockComponentC = class extends MockComponent {
      constructor() { super('component-c', ['component-a', 'component-b']); }
    };
  });

  afterEach(async () => {
    await registry.destroyAll();
  });

  describe('Component Registration', () => {
    test('should register component without dependencies', () => {
      registry.register('component-a', MockComponentA);

      expect(registry.components.has('component-a')).toBe(true);
      expect(registry.components.get('component-a').dependencies).toEqual([]);
    });

    test('should register component with dependencies', () => {
      registry.register('component-b', MockComponentB, ['component-a']);

      const registration = registry.components.get('component-b');
      expect(registration.dependencies).toEqual(['component-a']);
    });

    test('should throw error when registering duplicate component', () => {
      registry.register('component-a', MockComponentA);

      expect(() => {
        registry.register('component-a', MockComponentA);
      }).toThrow('Component component-a is already registered');
    });

    test('should allow overriding component with force flag', () => {
      registry.register('component-a', MockComponentA);

      const NewMockComponent = class extends MockComponent {
        constructor() { super('component-a-new'); }
      };

      expect(() => {
        registry.register('component-a', NewMockComponent, [], true);
      }).not.toThrow();
    });
  });

  describe('Dependency Resolution', () => {
    beforeEach(() => {
      registry.register('component-a', MockComponentA);
      registry.register('component-b', MockComponentB, ['component-a']);
      registry.register('component-c', MockComponentC, ['component-a', 'component-b']);
    });

    test('should resolve dependencies in correct order', () => {
      const order = registry.resolveDependencies();

      expect(order.indexOf('component-a')).toBeLessThan(order.indexOf('component-b'));
      expect(order.indexOf('component-b')).toBeLessThan(order.indexOf('component-c'));
    });

    test('should detect circular dependencies', () => {
      // Create circular dependency
      const MockComponentD = class extends MockComponent {
        constructor() { super('component-d', ['component-e']); }
      };
      const MockComponentE = class extends MockComponent {
        constructor() { super('component-e', ['component-d']); }
      };

      registry.register('component-d', MockComponentD, ['component-e']);
      registry.register('component-e', MockComponentE, ['component-d']);

      expect(() => {
        registry.resolveDependencies();
      }).toThrow('Circular dependency detected');
    });

    test('should throw error for missing dependencies', () => {
      const MockComponentWithMissingDep = class extends MockComponent {
        constructor() { super('component-missing', ['non-existent']); }
      };

      registry.register('component-missing', MockComponentWithMissingDep, ['non-existent']);

      expect(() => {
        registry.resolveDependencies();
      }).toThrow('Dependency non-existent not found');
    });
  });

  describe('Component Initialization', () => {
    beforeEach(() => {
      registry.register('component-a', MockComponentA);
      registry.register('component-b', MockComponentB, ['component-a']);
    });

    test('should initialize all components in dependency order', async () => {
      await registry.initializeAll();

      const componentA = registry.get('component-a');
      const componentB = registry.get('component-b');

      expect(componentA.initialized).toBe(true);
      expect(componentB.initialized).toBe(true);
      expect(registry.initOrder.indexOf('component-a')).toBeLessThan(
        registry.initOrder.indexOf('component-b')
      );
    });

    test('should initialize single component', async () => {
      await registry.initialize('component-a');

      const componentA = registry.get('component-a');
      expect(componentA.initialized).toBe(true);
      expect(registry.get('component-b')).toBeUndefined();
    });

    test('should initialize component with dependencies', async () => {
      await registry.initialize('component-b');

      const componentA = registry.get('component-a');
      const componentB = registry.get('component-b');

      expect(componentA.initialized).toBe(true);
      expect(componentB.initialized).toBe(true);
    });

    test('should handle initialization errors', async () => {
      const FailingComponent = class extends MockComponent {
        async init() {
          throw new Error('Init failed');
        }
      };

      registry.register('failing-component', FailingComponent);

      await expect(registry.initialize('failing-component')).rejects.toThrow('Init failed');
    });

    test('should not initialize already initialized component', async () => {
      await registry.initialize('component-a');
      const componentA = registry.get('component-a');
      const initSpy = jest.spyOn(componentA, 'init');

      await registry.initialize('component-a');
      expect(initSpy).not.toHaveBeenCalled();
    });
  });

  describe('Component Retrieval', () => {
    beforeEach(async () => {
      registry.register('component-a', MockComponentA);
      await registry.initializeAll();
    });

    test('should get initialized component', () => {
      const component = registry.get('component-a');
      expect(component).toBeInstanceOf(MockComponentA);
      expect(component.initialized).toBe(true);
    });

    test('should return undefined for non-existent component', () => {
      const component = registry.get('non-existent');
      expect(component).toBeUndefined();
    });

    test('should return undefined for uninitialized component', () => {
      registry.register('component-b', MockComponentB);
      const component = registry.get('component-b');
      expect(component).toBeUndefined();
    });

    test('should get all initialized components', () => {
      registry.register('component-b', MockComponentB);
      registry.initialize('component-b');

      const components = registry.getAll();
      expect(components.size).toBe(2);
      expect(components.has('component-a')).toBe(true);
      expect(components.has('component-b')).toBe(true);
    });
  });

  describe('Component Destruction', () => {
    beforeEach(async () => {
      registry.register('component-a', MockComponentA);
      registry.register('component-b', MockComponentB, ['component-a']);
      await registry.initializeAll();
    });

    test('should destroy single component', async () => {
      await registry.destroy('component-a');

      const componentA = registry.get('component-a');
      expect(componentA).toBeUndefined();
    });

    test('should destroy all components', async () => {
      await registry.destroyAll();

      expect(registry.instances.size).toBe(0);
      expect(registry.initOrder).toEqual([]);
    });

    test('should destroy components in reverse dependency order', async () => {
      const destroyOrder = [];

      const componentA = registry.get('component-a');
      const componentB = registry.get('component-b');

      const originalDestroyA = componentA.destroy.bind(componentA);
      const originalDestroyB = componentB.destroy.bind(componentB);

      componentA.destroy = async () => {
        destroyOrder.push('component-a');
        await originalDestroyA();
      };

      componentB.destroy = async () => {
        destroyOrder.push('component-b');
        await originalDestroyB();
      };

      await registry.destroyAll();

      expect(destroyOrder.indexOf('component-b')).toBeLessThan(
        destroyOrder.indexOf('component-a')
      );
    });

    test('should handle destruction errors gracefully', async () => {
      const componentA = registry.get('component-a');
      componentA.destroy = async () => {
        throw new Error('Destroy failed');
      };

      // Should not throw, but should log error
      await expect(registry.destroyAll()).resolves.not.toThrow();
    });
  });

  describe('Event Integration', () => {
    test('should emit registry events', async () => {
      const events = [];

      registry.on('component-registered', data => events.push(['registered', data]));
      registry.on('component-initialized', data => events.push(['initialized', data]));
      registry.on('component-destroyed', data => events.push(['destroyed', data]));

      registry.register('component-a', MockComponentA);
      await registry.initialize('component-a');
      await registry.destroy('component-a');

      expect(events).toEqual([
        ['registered', { name: 'component-a' }],
        ['initialized', { name: 'component-a' }],
        ['destroyed', { name: 'component-a' }]
      ]);
    });
  });

  describe('Registry State', () => {
    test('should track registry state', () => {
      expect(registry.getState()).toEqual({
        registered: 0,
        initialized: 0,
        failed: 0
      });

      registry.register('component-a', MockComponentA);
      expect(registry.getState().registered).toBe(1);
    });

    test('should provide component information', () => {
      registry.register('component-a', MockComponentA);
      registry.register('component-b', MockComponentB, ['component-a']);

      const info = registry.getComponentInfo('component-b');
      expect(info).toEqual({
        name: 'component-b',
        dependencies: ['component-a'],
        initialized: false,
        instance: null
      });
    });

    test('should list all registered components', () => {
      registry.register('component-a', MockComponentA);
      registry.register('component-b', MockComponentB, ['component-a']);

      const list = registry.listComponents();
      expect(list).toEqual(['component-a', 'component-b']);
    });
  });
});
