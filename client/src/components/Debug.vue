<template>
  <div style="padding:10px">
    <div>{{ uuid }}</div>
    <div>{{ ip }}</div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data: () => ({
    uuid: null,
    ip: null,
  }),
  created() {
    this.get()
  },
  methods: {
    get() {
      axios.get('/debug')
        .then((response) => {
          this.uuid = response.data.uuid
          this.ip = response.data.ip
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => location.reload())
          else console.log(error.response)
        })
    },
  }
}
</script>