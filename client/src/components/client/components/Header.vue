<template>
  <div>
    <v-tabs v-model="headerTab" show-arrows background-color="#9b59b6" color="white" slider-color="white" slot="extension" class="elevation-2">
      <v-tabs-slider></v-tabs-slider>
      <v-tab @click="tabClient()"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>CLIENT</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabStructure()" :disabled="treeviewMode != 'objects' || treeviewSelected['type'] != 'Table'"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-dice-d6</v-icon>Structure</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabContent()" :disabled="treeviewMode != 'objects' || !['Table','View'].includes(treeviewSelected['type'])"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-bars</v-icon>Content</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabInfo(treeviewSelected['type'].toLowerCase())" :disabled="treeviewMode != 'objects' || !['Table','View','Trigger','Function','Procedure','Event'].includes(treeviewSelected['type'])"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-cube</v-icon>Info</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-spacer></v-spacer>
      <v-tab title="Query History" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-history</v-icon></span></v-tab>
      <v-tab title="Saved Queries" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-star</v-icon></span></v-tab>
      <v-tab @click="tabObjects()" :disabled="treeviewMode != 'objects' || database.length == 0" title="Schema Objects" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-cubes</v-icon></span></v-tab>
      <v-tab :disabled="treeviewMode == 'servers'" title="User Rights" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-shield-alt</v-icon></span></v-tab>
    </v-tabs>
  </div>
</template>

<script>
import EventBus from '../js/event-bus'
import { mapFields } from '../js/map-fields'

export default {
  data() {
    return {
    }
  },
  computed: {
    ...mapFields([
      'headerTab',
      'headerTabSelected',
      'treeview',
      'treeviewMode',
      'treeviewSelected',
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
  },
}
</script>