export class AsyncQueue {
  constructor(maxsize = Infinity) {
    this.queue = [];
    this.waiters = [];
    this.maxsize = maxsize;
  }


  async put(item) {
    while (this.queue.length >= this.maxsize) {
      await new Promise(resolve => this.waiters.push(resolve));
    }

    if (this.waiters.length > 0) {
      const resolve = this.waiters.shift();
      resolve(item);
    } else {
        this.queue.push(item);
    }
  }

  async get() {
    if (this.queue.length > 0) {
      return this.queue.shift();
    } else {
      return new Promise(resolve => {
        this.waiters.push(resolve);
      });
    }
  }

  isEmpty() {
    return this.queue.length === 0;
  }

  isFull() {
    return this.queue.length >= this.maxsize;
  }
}
