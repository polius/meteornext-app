<template>
  <div>
    <v-tabs show-arrows background-color="#9b59b6" color="white" v-model="headerTab" slider-color="white" slot="extension" class="elevation-2">
      <v-tabs-slider></v-tabs-slider>
      <v-tab @click="tabClient()"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>CLIENT</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabStructure()" :disabled="treeviewMode != 'objects' || treeview.length == 0 || ('children' in treeviewSelected) || treeviewSelected['type'] != 'Table'"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-dice-d6</v-icon>Structure</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabContent()" :disabled="treeviewMode != 'objects' || treeview.length == 0 || ('children' in treeviewSelected) || !(['Table','View'].includes(treeviewSelected['type']))"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-bars</v-icon>Content</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-tab @click="tabInfo(treeviewSelected['type'].toLowerCase())" :disabled="treeviewMode != 'objects' || treeview.length == 0 || ('children' in treeviewSelected) || !(['Table','View','Trigger','Function','Procedure','Event'].includes(treeviewSelected['type']))"><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-italic</v-icon>Info</span></v-tab>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-spacer></v-spacer>
      <v-tab title="Query History" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-history</v-icon></span></v-tab>
      <v-tab title="Saved Queries" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-star</v-icon></span></v-tab>
      <v-tab :disabled="treeviewMode == 'servers'" title="User Rights" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-shield-alt</v-icon></span></v-tab>
    </v-tabs>
  </div>
</template>

<script>
import EventBus from '../js/event-bus'

export default {
  data() {
    return {
    }
  },
  mounted () {
    // EventBus.$on(‘EVENT_NAME’, function (payLoad) {
    //   ...
    // });
  },
  computed: {
    headerTab () { return this.$store.getters['client/connection'].headerTab },
    treeview () { return this.$store.getters['client/connection'].treeview },
    treeviewMode () { return this.$store.getters['client/connection'].treeviewMode },
    treeviewSelected () { return this.$store.getters['client/connection'].treeviewSelected },
    structureHeaders () { return this.$store.getters['client/connection'].structureHeaders },
    contentTableSelected () { return this.$store.getters['client/connection'].contentTableSelected },
  },
  watch: {
    headerTab(data) {
      this.$store.dispatch('client/update', { key: 'headerTab', value: data})
    }
  },
  methods: {
    tabClient() {
      this.$store.dispatch('client/update', { key: 'headerTab', value: 0 })
      // setTimeout(() => { this.editor.focus() }, 100)
    },
    tabStructure() {
      if (this.structureHeaders.length == 0) EventBus.$emit('getStructure')
    },
    tabContent() {
      if (this.contentTableSelected != this.treeviewSelected['name']) EventBus.$emit('getContent')
    },
    tabInfo() {
      // if (this.infoEditor == null) {
      //   this.infoEditor = ace.edit("infoEditor", {
      //     mode: "ace/mode/sql",
      //     theme: "ace/theme/monokai",
      //     fontSize: 14,
      //     showPrintMargin: false,
      //     wrap: true,
      //     readOnly: true,
      //     showLineNumbers: false
      //   });
      //   this.infoEditor.container.addEventListener("keydown", (e) => {
      //     // - Increase Font Size -
      //     if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
      //       let size = parseInt(this.infoEditor.getFontSize(), 10) || 12
      //       this.infoEditor.setFontSize(size + 1)
      //       e.preventDefault()
      //     }
      //     // - Decrease Font Size -
      //     else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
      //       let size = parseInt(this.infoEditor.getFontSize(), 10) || 12
      //       this.infoEditor.setFontSize(Math.max(size - 1 || 1))
      //       e.preventDefault()
      //     }
      //   }, false);
      // }
      EventBus.$emit('getInfo')
    }
  },
}
</script>