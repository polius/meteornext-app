<template>
  <div style="height:100%">
    <Client v-show="headerTabSelected == 'client'" />
    <Structure v-show="headerTabSelected == 'structure'" />
    <Content v-show="headerTabSelected == 'content'" />
    <Info v-show="headerTabSelected.startsWith('info')" />
    <Objects v-show="headerTabSelected.startsWith('objects')" />
  </div>
</template>

<script>
import { mapFields } from '../js/map-fields'

import Client from './main/Client'
import Content from './main/Content'
import Structure from './main/Structure'
import Info from './main/Info'
import Objects from './main/Objects'

export default {
  data() {
    return {
    }
  },
  components: { Client, Content, Structure, Info, Objects },
  computed: {
    ...mapFields([
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {

  },
  methods: {
  }
}
</script>