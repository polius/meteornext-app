<template>
  <div style="display:grid; height:100%; align-content:center; text-align:center">
      <v-avatar size="200" style="margin-left:auto; margin-right:auto"><v-img src="../assets/logo.png"></v-img></v-avatar>
      <div class="text-h2 font-weight-medium" style="margin:40px; font-size:3.2rem!important">Meteor Next</div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({}),
  created() {
    this.checkLogin()
  },
  methods: {
    checkLogin() {
      axios.get('/login/check')
        .catch(() => {
          this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        })
    }
  }
}
</script>