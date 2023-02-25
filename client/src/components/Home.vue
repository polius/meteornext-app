<template>
  <div>
    <div style="position:fixed; top:50%; left: 50%; transform: translate(-50%, -50%); width:100%">
      <transition appear appear-active-class="logo-transition">
        <v-avatar size="100" style="margin-left:auto; margin-right:auto; display:inherit"><v-img src="../assets/logo.png"></v-img></v-avatar>
      </transition>
      <transition appear appear-active-class="title-transition">
        <div class="text-h2" style="margin:20px; font-size:3.2rem!important; font-weight:400; text-align:center">Meteor Next<span style="margin-left:12px; font-family: Consolas,monaco,monospace; font-size:14px;">v{{ version }}</span></div>
      </transition>
    </div>
    <div class="font-weight-light" style="position:fixed; bottom:0; width:100%; margin-bottom:2vh; font-size:14px; text-align:center">Copyright © {{ new Date().getFullYear() }} <a style="color: white" href="https://www.meteornext.io" target="_blank">Meteor Next</a></div>
  </div>
</template>

<style scoped>
.logo-transition {
  animation: logo-animation 0.5s;
}
@keyframes logo-animation {
  from {
    bottom: 50px;
    left: 50px;
  }
  to {
    bottom: 0px;
    left: 0px;
  }
}
.title-transition {
  animation-delay: 1.5s;
  animation: title-animation 1.5s;
}
@keyframes title-animation {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>

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