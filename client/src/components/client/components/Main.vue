<template>
  <div style="height:100%">
    <Client v-show="headerTabSelected == 'client'" />
    <Structure v-if="mounted" v-show="headerTabSelected == 'structure'" />
    <Content v-if="mounted" v-show="headerTabSelected == 'content'" />
    <Info v-if="mounted" v-show="headerTabSelected.startsWith('info')" />
    <Objects v-if="mounted" v-show="headerTabSelected.startsWith('objects')" />
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
      mounted: false
    }
  },
  components: { Client, Content, Structure, Info, Objects },
  computed: {
    ...mapFields([
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    setTimeout(() => { this.mounted = true }, 1000);
  },
  methods: {
  }
}
</script>