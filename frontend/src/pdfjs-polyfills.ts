export function installPdfPolyfills(): void {
  const mapProto = Map.prototype as Map<unknown, unknown> & {
    getOrInsert?: (key: unknown, value: unknown) => unknown;
    getOrInsertComputed?: (key: unknown, callback: (key: unknown) => unknown) => unknown;
  };
  if (typeof mapProto.getOrInsert !== 'function') {
    mapProto.getOrInsert = function (key, value) {
      if (!this.has(key)) this.set(key, value);
      return this.get(key);
    };
  }
  if (typeof mapProto.getOrInsertComputed !== 'function') {
    mapProto.getOrInsertComputed = function (key, callback) {
      if (!this.has(key)) this.set(key, callback(key));
      return this.get(key);
    };
  }

  const weakProto = WeakMap.prototype as WeakMap<object, unknown> & {
    getOrInsert?: (key: object, value: unknown) => unknown;
    getOrInsertComputed?: (key: object, callback: (key: object) => unknown) => unknown;
  };
  if (typeof weakProto.getOrInsert !== 'function') {
    weakProto.getOrInsert = function (key, value) {
      if (!this.has(key)) this.set(key, value);
      return this.get(key);
    };
  }
  if (typeof weakProto.getOrInsertComputed !== 'function') {
    weakProto.getOrInsertComputed = function (key, callback) {
      if (!this.has(key)) this.set(key, callback(key));
      return this.get(key);
    };
  }
}

installPdfPolyfills();
