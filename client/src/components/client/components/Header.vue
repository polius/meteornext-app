<template>
  <div>
    <v-tabs v-model="headerTab" show-arrows background-color="#8e44ad" color="white" slider-color="white" slot="extension" class="elevation-2">
      <v-tabs-slider></v-tabs-slider>
      <v-tab @click="tabClient"><span class="pl-2 pr-2" style="min-width:100px"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>CLIENT</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabStructure" :disabled="sidebarMode != 'objects' || sidebarSelected.length != 1 || 'children' in sidebarSelected[0] ||  sidebarSelected[0]['type'] != 'Table'"><span class="pl-2 pr-2" style="min-width:130px"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-dice-d6</v-icon>Structure</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabContent" :disabled="sidebarMode != 'objects' || sidebarSelected.length != 1 || 'children' in sidebarSelected[0] || !['Table','View'].includes(sidebarSelected[0]['type'])"><span class="pl-2 pr-2" style="min-width:112px"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-bars</v-icon>Content</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabInfo" :disabled="sidebarMode != 'objects' || sidebarSelected.length != 1 || 'children' in sidebarSelected[0] || !['Table','View','Trigger','Function','Procedure','Event'].includes(sidebarSelected[0]['type'])"><span class="pl-2 pr-2" style="min-width:100px"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-cube</v-icon>Info</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-spacer></v-spacer>
      <v-tab @click="tabSettings" title="Settings" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-cog</v-icon></span></v-tab>
      <v-tab @click="tabHistory" title="Query History" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-history</v-icon></span></v-tab>
      <v-tab @click="tabSaved" title="Saved Queries" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-star</v-icon></span></v-tab>
      <v-tab @click="tabObjects" :disabled="sidebarMode != 'objects' || database.length == 0" title="Schema Objects" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small style="font-size:17px; margin-top:3px;">fas fa-cube</v-icon></span></v-tab>
      <v-tab @click="tabProcesslist" :disabled="sidebarMode == 'servers'" title="Processlist" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-server</v-icon></span></v-tab>
      <v-tab @click="tabRights" :disabled="sidebarMode == 'servers'" title="User Rights" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-shield-alt</v-icon></span></v-tab>
    </v-tabs>
    <!---------------->
    <!-- COMPONENTS -->
    <!---------------->
    <Settings />
    <History />
    <Saved />
    <Processlist />
    <Rights />
  </div>
</template>

<script>
import EventBus from '../js/event-bus'
import { mapFields } from '../js/map-fields'

import Settings from './header/Settings'
import History from './header/History'
import Saved from './header/Saved'
import Processlist from './header/Processlist'
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
  components: { Settings, History, Saved, Processlist, Rights },
  methods: {
    tabClient() {
      this.headerTab = 0
      this.headerTabSelected = 'client'
      this.editor.focus()
    },
    tabStructure() {
      this.headerTabSelected = 'structure'
      EventBus.$emit('get-structure', false)
    },
    tabContent() {
      this.headerTabSelected = 'content'
      EventBus.$emit('get-content', false)
    },
    tabInfo() {
      const object = this.sidebarSelected[0]['type'].toLowerCase()
      this.headerTabSelected = 'info_' + object
      EventBus.$emit('get-info', object)
    },
    tabObjects() {
      this.headerTabSelected = 'objects'
      new Promise((resolve, reject) => { EventBus.$emit('get-objects', resolve, reject) })
    },
    tabHistory() {
      EventBus.$emit('show-history')
    },
    tabSaved() {
      EventBus.$emit('show-saved')
    },
    tabProcesslist() {
      EventBus.$emit('show-processlist')
    },
    tabRights() {
      EventBus.$emit('show-rights')
    },
    tabSettings() {
      EventBus.$emit('show-settings')
    },
  },
}
</script>