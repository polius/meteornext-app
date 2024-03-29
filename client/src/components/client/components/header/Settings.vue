<template>
  <div>
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-cog</v-icon>SETTINGS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @loading="loading" @disabled="loading" @click="saveSettings" color="#00b16a" style="margin-right:10px;"><v-icon small style="margin-right:10px">fas fa-save</v-icon>Save</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:10px 15px 0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" @submit.prevent style="margin-bottom:15px;">
                  <v-text-field filled v-model="editorFontSize" @keyup.enter="saveSettings" label="Editor Font Size" :rules="[v => v == parseInt(v) && v > 0 || '']" hide-details style="margin-top:10px"></v-text-field>
                  <v-checkbox v-model="secureMode" color="#00b16a" style="margin-top:15px" hide-details>
                    <template v-slot:label>
                      <div style="margin-left:2px">
                        <div class="white--text">Secure Mode</div>
                        <div class="font-weight-regular caption" style="font-size:0.85rem !important">All modifications done in CLIENT (editing SELECT results) and CONTENT will require a confirmation before proceeding.</div>
                      </div>
                    </template>
                  </v-checkbox>
                  <v-divider style="margin-top:15px"></v-divider>
                  <div class="subtitle-1 font-weight-regular white--text" style="margin-top:12px; margin-bottom:10px; margin-left:2px">SHORTCUTS</div>
                  <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection suppressFieldDotNotation suppressContextMenu preventDefaultOnContextMenu oncontextmenu="return false" @grid-ready="onGridReady" style="width:100%; height:60vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="header" :rowData="shortcuts"></ag-grid-vue>
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
import axios from 'axios'
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'
import {AgGridVue} from "ag-grid-vue";

export default {
  data() {
    return {
      dialog: false,
      loading: false,
      editorFontSize: '14',
      secureMode: true,
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
        { command: 'Save Editor', binding: 'Ctrl + S', scope: 'Client Editor' },
        { command: 'Increase Font Size', binding: 'Ctrl + +', scope: 'Client Editor' },
        { command: 'Decrease Font Size', binding: 'Ctrl + -', scope: 'Client Editor' },
        { command: 'Toggle Comment', binding: 'Ctrl + Shift + C', scope: 'Client Editor' },
      ],
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'settings',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('show-settings', this.showDialog)
    // Build shortcuts
    const isMacLike = navigator.userAgent.match(/(Mac|iPhone|iPod|iPad)/i) ? true : false
    if (isMacLike) {
      for (let i = 0; i < this.shortcuts.length; ++i) this.shortcuts[i]['binding'] = this.shortcuts[i]['binding'].replace('Ctrl', '⌘')
    }
  },
  watch: {
    dialog: function(value) {
      this.dialogOpened = value
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 7}
        this.headerTab = tab[this.headerTabSelected]
      }
    },
  },
  methods: {
    showDialog() {
      this.dialog = true
      this.getSettings()
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
    getSettings() {
      if ('font_size' in this.settings) this.editorFontSize = this.settings['font_size']
      if ('secure_mode' in this.settings) this.secureMode = parseInt(this.settings['secure_mode'])
    },
    saveSettings() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required login fields are filled out correctly', '#EF5354')
        return
      }
      this.loading = true
      const payload = {
        font_size: this.editorFontSize,
        secure_mode: this.secureMode,
      }
      axios.put('/client/settings', payload)
        .then((response) => {
          this.settings['font_size'] = payload['font_size']
          this.settings['secure_mode'] = payload['secure_mode'] ? 1 : 0
          EventBus.$emit('send-notification', response.data.message, '#00b16a', 1)
          EventBus.$emit('settings-saved')
          this.dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
  },
}
</script>