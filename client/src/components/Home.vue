<template>
  <v-container>
    <v-layout text-center wrap>
      <v-flex xs12 style="margin-top:100px;">
        <v-avatar :size="200" ><v-img :src="require('../assets/logo.png')" class="my-3" contain height="200"></v-img></v-avatar>
      </v-flex>

      <v-flex mb-4 style="margin-top:30px;">
        <h1 class="display-2 font-weight-bold mb-3"><b>Meteor</b> Next</h1>
      </v-flex>
    </v-layout>
  </v-container>
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
        .then(() => {})
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    }
  }
}
</script>