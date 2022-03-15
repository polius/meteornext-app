<template>
  <div style="display:grid; height:100%; align-content:center; text-align:center">
    <v-avatar size="100" style="margin-left:auto; margin-right:auto"><v-img src="../assets/logo.png"></v-img></v-avatar>
    <div class="text-h2" style="margin:15px; font-size:3.2rem!important; font-weight:400">Meteor Next<span class="text-body-1 font-weight-light" style="margin-top:10px; margin-left:10px">{{ version }}</span></div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    version: '',
  }),
  created() {
    this.getVersion()
  },
  methods: {
    getVersion() {
      axios.get('/version')
        .then((response) => {
          this.version = response.data.version
        })
        .catch(() => {
          this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        })
    }
  }
}
</script>