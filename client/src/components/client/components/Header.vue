<template>
  <div>
    <v-tabs v-model="headerTab" show-arrows background-color="#9b59b6" color="white" slider-color="white" slot="extension" class="elevation-2">
      <v-tabs-slider></v-tabs-slider>
      <v-tab @click="tabClient"><span class="pl-2 pr-2" style="min-width:100px"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>CLIENT</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabStructure" :disabled="sidebarMode != 'objects' || sidebarSelected['type'] != 'Table'"><span class="pl-2 pr-2" style="min-width:130px"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-dice-d6</v-icon>Structure</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabContent" :disabled="sidebarMode != 'objects' || !['Table','View'].includes(sidebarSelected['type'])"><span class="pl-2 pr-2" style="min-width:112px"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-bars</v-icon>Content</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabInfo(sidebarSelected['type'].toLowerCase())" :disabled="sidebarMode != 'objects' || !['Table','View','Trigger','Function','Procedure','Event'].includes(sidebarSelected['type'])"><span class="pl-2 pr-2" style="min-width:100px"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-cube</v-icon>Info</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-spacer></v-spacer>
      <v-tab @click="tabHistory" title="Query History" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-history</v-icon></span></v-tab>
      <v-tab @click="tabSaved" title="Saved Queries" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-star</v-icon></span></v-tab>
      <v-tab @click="tabObjects" :disabled="sidebarMode != 'objects' || database.length == 0" title="Schema Objects" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small style="font-size:17px; margin-top:3px;">fas fa-cubes</v-icon></span></v-tab>
      <v-tab :disabled="sidebarMode == 'servers'" title="Processlist" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-server</v-icon></span></v-tab>
      <v-tab @click="tabRights" :disabled="sidebarMode == 'servers'" title="User Rights" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-shield-alt</v-icon></span></v-tab>
    </v-tabs>
    <!---------------->
    <!-- COMPONENTS -->
    <!---------------->
    <History />
    <Saved />
    <Rights />
  </div>
</template>

<script>
import EventBus from '../js/event-bus'
import { mapFields } from '../js/map-fields'

import History from './header/History'
import Saved from './header/Saved'
import Rights from './header/Rights'

export default {
  data() {
    return {
    }
  },
  computed: {
    ...mapFields([
      'headerTab',
      'headerTabSelected',
      'sidebar',
      'sidebarMode',
      'sidebarSelected',
      'structureHeaders',
      'contentHeaders',
      'infoHeaders',
      'objectsHeaders',
      'database',
    ], { path: 'client/connection' }),
    ...mapFields([
      'editor',
    ], { path: 'client/components' }),
  },
  components: { History, Saved, Rights },
  methods: {
    tabClient() {
      this.headerTab = 0
      this.headerTabSelected = 'client'
      this.editor.focus()
    },
    tabStructure() {
      this.headerTabSelected = 'structure'
      if (this.structureHeaders.columns.length == 0) EventBus.$emit('GET_STRUCTURE')
    },
    tabContent() {
      this.headerTabSelected = 'content'
      if (this.contentHeaders.length == 0) EventBus.$emit('GET_CONTENT')
    },
    tabInfo(object) {
      this.headerTabSelected = 'info_' + object
      if (this.infoHeaders[object + 's'].length == 0) EventBus.$emit('GET_INFO', object)
    },
    tabObjects() {
      this.headerTabSelected = 'objects'
      if (this.objectsHeaders.databases.length == 0) {
        new Promise((resolve, reject) => { EventBus.$emit('GET_OBJECTS', resolve, reject) })
      }
    },
    tabHistory() {
      EventBus.$emit('SHOW_HISTORY')
    },
    tabSaved() {
      EventBus.$emit('SHOW_SAVED')
    },
    tabRights() {
      EventBus.$emit('SHOW_RIGHTS')
    },
  },
}
</script>