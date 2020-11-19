<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-cog</v-icon>Settings</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @loading="loading" @disabled="loading" @click="saveSettings" color="primary" style="margin-right:10px;">Save</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:10px 15px 0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-text-field outlined v-model="editorFontSize" label="Editor Font Size" :rules="[v => v == parseInt(v) || '']" hide-details style="margin-top:10px"></v-text-field>
                  <div class="subtitle-1 font-weight-regular white--text" style="margin-top:12px; margin-bottom:10px; margin-left:2px">SHORTCUTS</div>
                  <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection suppressContextMenu preventDefaultOnContextMenu @grid-ready="onGridReady" style="width:100%; height:60vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="header" :rowData="shortcuts"></ag-grid-vue>
                  <!-- <div class="body-1"><v-chip label>Ctrl + T</v-chip> Open</div> -->
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped src="@/styles/agGridVue.css"></style>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'
import {AgGridVue} from "ag-grid-vue";

export default {
  data() {
    return {
      dialog: false,
      loading: false,
      editorFontSize: '14',
      // AG Grid
      gridApi: null,
      columnApi: null,
      header: [
        { headerName: 'Command', colId: 'command', field: 'command', sortable: false, filter: false, resizable: false, editable: false },
        { headerName: 'Key Binding', colId: 'binding', field: 'binding', sortable: false, filter: false, resizable: false, editable: false },
        { headerName: 'Key Scope', colId: 'scope', field: 'scope', sortable: false, filter: false, resizable: false, editable: false },
      ],
      shortcuts: [
        { command: 'New Connection', binding: 'Ctrl + .', scope: 'App' },
        { command: 'Close Connection', binding: 'Ctrl + ,', scope: 'App' },
        { command: 'Next Connection', binding: 'Ctrl + P', scope: 'App' },
        { command: 'Previous Connection', binding: 'Ctrl + O', scope: 'App' },
        { command: 'Change Connection [1-9]', binding: 'Ctrl + [1-9]', scope: 'App' },
        { command: 'Run Query', binding: 'Ctrl + R', scope: 'Client Editor' },
        { command: 'Explain Query', binding: 'Ctrl + E', scope: 'Client Editor' },
        { command: 'Minify Query', binding: 'Ctrl + M', scope: 'Client Editor' },
        { command: 'Beautify Query', binding: 'Ctrl + B', scope: 'Client Editor' },
        { command: 'Save Query', binding: 'Ctrl + S', scope: 'Client Editor' },
        { command: 'Increase Font Size', binding: 'Ctrl + +', scope: 'Client Editor' },
        { command: 'Decrease Font Size', binding: 'Ctrl + -', scope: 'Client Editor' },
      ],
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-settings', this.showDialog)
    // Build shortcuts
    const isMacLike = navigator.platform.match(/(Mac|iPhone|iPod|iPad)/i) ? true : false
    if (isMacLike) {
      for (let i = 0; i < this.shortcuts.length; ++i) this.shortcuts[i]['binding'] = this.shortcuts[i]['binding'].replace('Ctrl', '⌘')
    }
  },
  watch: {
    dialog: function(value) {
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
      }
    },
  },
  methods: {
    showDialog() {
      this.dialog = true
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      this.resizeTable()
    },
    resizeTable() {
      this.$nextTick(() => {
        if (this.gridApi != null) this.gridApi.sizeColumnsToFit()
      })
    },
    saveSettings() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required login fields are filled out correctly', 'error')
        return
      }
    },
  },
}
</script>