export function mapFields (props = [], {path} = {}) {
  return props.reduce((obj, prop) => {
    obj[prop] = {
      get() {
        return this.$store.getters[path][prop]
      },
      set(value) {
        this.$store.commit(path, { k: prop, v: value })
      }
    }
    return obj
  }, {})
}