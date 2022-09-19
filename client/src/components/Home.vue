<template>
  <div style="display:grid; height:100vh; align-content:center; text-align:center">
    <transition appear appear-active-class="logo-transition">
      <v-avatar size="100" style="margin-left:auto; margin-right:auto"><v-img src="../assets/logo.png"></v-img></v-avatar>
    </transition>
    <transition appear appear-active-class="title-transition">
      <div class="text-h2" style="margin:20px; font-size:3.2rem!important; font-weight:400">Meteor Next<span class="text-body-1 font-weight-light" style="margin-top:10px; margin-left:10px">{{ version }}</span></div>
    </transition>
    <!-- <div class="font-weight-light" style="position:fixed; bottom:0; width:100%; margin-bottom:2vh; font-size:14px">Meteor Next is a registered trademark of <a style="color: white" href="https://www.poliuscorp.com" target="_blank">PoliusCorp</a>.</div> -->
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