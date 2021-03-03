<template>
  <div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
  }),
  created() {
    this.checkAdmin()
  },
  methods: {
    checkAdmin() {
      axios.get('/admin')
        .catch(() => {
          this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        })
    }
  }
}
</script>