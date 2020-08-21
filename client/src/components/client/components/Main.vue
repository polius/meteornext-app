<template>
  <div style="height:100%">
    <Client v-show="headerTab == 0" />
    <Structure v-show="headerTab == 1" />
    <Content v-show="headerTab == 2" />
    <Info v-show="headerTab == 3" />
  </div>
</template>

<script>
import Client from './main/Client'
import Content from './main/Content'
import Structure from './main/Structure'
import Info from './main/Info'

export default {
  data() {
    return {
    }
  },
  components: { Client, Content, Structure, Info },
  computed: {
    headerTab () { return this.$store.getters['client/connection'].headerTab },
  },
  mounted() {

  },
  methods: {
  }
}
</script>