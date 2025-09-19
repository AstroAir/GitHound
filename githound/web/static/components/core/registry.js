/**
 * Component Registry
 *
 * Manages component registration, dependency resolution, and initialization order.
 */

export class ComponentRegistry {
  constructor() {
    this.components = new Map();
    this.instances = new Map();
    this.initializationOrder = [];
    this.initialized = false;
  }

  /**
   * Register a component class
   */
  register(name, ComponentClass, options = {}) {
    if (this.components.has(name)) {
      console.warn(`Component ${name} is already registered`);
      return;
    }

    this.components.set(name, {
      ComponentClass,
      options,
      dependencies: options.dependencies || []
    });

    console.log(`Registered component: ${name}`);
  }

  /**
   * Get a component instance
   */
  get(name) {
    return this.instances.get(name);
  }

  /**
   * Check if a component is registered
   */
  has(name) {
    return this.components.has(name);
  }

  /**
   * Create an instance of a component
   */
  createInstance(name, options = {}) {
    const componentDef = this.components.get(name);
    if (!componentDef) {
      throw new Error(`Component ${name} is not registered`);
    }

    const mergedOptions = { ...componentDef.options, ...options };
    const instance = new componentDef.ComponentClass(name, mergedOptions);

    // Add dependencies to the instance
    componentDef.dependencies.forEach(dep => {
      instance.addDependency(dep);
    });

    this.instances.set(name, instance);
    return instance;
  }

  /**
   * Initialize all registered components in dependency order
   */
  async initializeAll() {
    if (this.initialized) {
      console.warn('Components already initialized');
      return;
    }

    console.log('Starting component initialization...');

    try {
      // Create all instances first
      for (const [name] of this.components) {
        if (!this.instances.has(name)) {
          this.createInstance(name);
        }
      }

      // Resolve initialization order based on dependencies
      const order = this.resolveInitializationOrder();
      this.initializationOrder = order;

      // Initialize components in order
      for (const name of order) {
        const instance = this.instances.get(name);
        if (instance && !instance.initialized) {
          console.log(`Initializing component: ${name}`);
          await instance.init();
        }
      }

      this.initialized = true;
      console.log('All components initialized successfully');

      // Emit global initialization event
      this.emit('allInitialized');
    } catch (error) {
      console.error('Failed to initialize components:', error);
      throw error;
    }
  }

  /**
   * Resolve component initialization order based on dependencies
   */
  resolveInitializationOrder() {
    const visited = new Set();
    const visiting = new Set();
    const order = [];

    const visit = name => {
      if (visited.has(name)) { return; }
      if (visiting.has(name)) {
        throw new Error(`Circular dependency detected involving component: ${name}`);
      }

      visiting.add(name);

      const componentDef = this.components.get(name);
      if (componentDef) {
        // Visit dependencies first
        componentDef.dependencies.forEach(dep => {
          if (this.components.has(dep)) {
            visit(dep);
          } else {
            console.warn(`Dependency ${dep} for component ${name} is not registered`);
          }
        });
      }

      visiting.delete(name);
      visited.add(name);
      order.push(name);
    };

    // Visit all components
    for (const [name] of this.components) {
      visit(name);
    }

    return order;
  }

  /**
   * Destroy all components in reverse order
   */
  destroyAll() {
    console.log('Destroying all components...');

    // Destroy in reverse order
    const reverseOrder = [...this.initializationOrder].reverse();

    for (const name of reverseOrder) {
      const instance = this.instances.get(name);
      if (instance && !instance.destroyed) {
        console.log(`Destroying component: ${name}`);
        instance.destroy();
      }
    }

    this.instances.clear();
    this.initialized = false;
    console.log('All components destroyed');
  }

  /**
   * Reload a specific component
   */
  async reload(name) {
    const instance = this.instances.get(name);
    if (instance) {
      instance.destroy();
    }

    const newInstance = this.createInstance(name);
    await newInstance.init();

    console.log(`Component ${name} reloaded`);
    return newInstance;
  }

  /**
   * Get component status information
   */
  getStatus() {
    const status = {
      registered: this.components.size,
      initialized: 0,
      failed: 0,
      components: {}
    };

    for (const [name, instance] of this.instances) {
      const componentStatus = {
        initialized: instance.initialized,
        destroyed: instance.destroyed,
        dependencies: instance.dependencies,
        dependenciesSatisfied: instance.areDependenciesSatisfied()
      };

      status.components[name] = componentStatus;

      if (instance.initialized) {
        status.initialized++;
      } else if (instance.destroyed) {
        status.failed++;
      }
    }

    return status;
  }

  /**
   * Emit a global event to all components
   */
  emit(event, data = null) {
    for (const [name, instance] of this.instances) {
      if (instance.initialized) {
        instance.emit(event, data);
      }
    }
  }

  /**
   * Wait for a component to be initialized
   */
  async waitFor(name, timeout = 5000) {
    return new Promise((resolve, reject) => {
      const instance = this.instances.get(name);

      if (!instance) {
        reject(new Error(`Component ${name} is not registered`));
        return;
      }

      if (instance.initialized) {
        resolve(instance);
        return;
      }

      const timeoutId = setTimeout(() => {
        reject(new Error(`Timeout waiting for component ${name} to initialize`));
      }, timeout);

      instance.on('initialized', () => {
        clearTimeout(timeoutId);
        resolve(instance);
      });
    });
  }

  /**
   * Get dependency graph for debugging
   */
  getDependencyGraph() {
    const graph = {};

    for (const [name, componentDef] of this.components) {
      graph[name] = {
        dependencies: componentDef.dependencies,
        dependents: []
      };
    }

    // Calculate dependents
    for (const [name, componentDef] of this.components) {
      componentDef.dependencies.forEach(dep => {
        if (graph[dep]) {
          graph[dep].dependents.push(name);
        }
      });
    }

    return graph;
  }
}

// Create global registry instance
export const registry = new ComponentRegistry();

// Make it available globally for debugging
if (typeof window !== 'undefined') {
  window.GitHound = window.GitHound || {};
  window.GitHound.registry = registry;
}

export default registry;
