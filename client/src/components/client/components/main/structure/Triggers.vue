<template>
  <div style="height:100%">
    <!-------------->
    <!-- Triggers -->
    <!--------------->
    <div style="height:calc(100% - 84px)">
      <ag-grid-vue ref="agGridStructureTriggers" suppressDragLeaveHidesColumns suppressFieldDotNotation suppressContextMenu preventDefaultOnContextMenu oncontextmenu="return false" @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" @cell-clicked="onCellClicked" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowDragManaged="true" suppressMoveWhenRowDragging="true" rowHeight="35" headerHeight="35" rowSelection="single" rowDeselection="true" stopEditingWhenCellsLoseFocus="true" :columnDefs="structureHeaders.triggers" :rowData="structureItems.triggers"></ag-grid-vue>
    </div>
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn @click="refreshTriggers" text small title="Refresh Triggers" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
          <v-btn @click="addTrigger" text small title="New Trigger" style="height:30px; min-width:36px; margin-top:1px; margin-left:3px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
          <v-btn :disabled="!selectedRows" @click="removeTrigger" text small title="Remove Trigger" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            <v-icon v-if="bottomBar.structure.triggers['status'] == 'success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:1px; padding-right:7px;">fas fa-check-circle</v-icon>
            <v-icon v-else-if="bottomBar.structure.triggers['status'] == 'failure'" title="Failed" small style="color:#EF5354; padding-bottom:1px; padding-right:7px;">fas fa-times-circle</v-icon>
            <span :title="bottomBar.structure.triggers['text']">{{ bottomBar.structure.triggers['text'] }}</span>
          </div>
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.structure.triggers['info'] }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:3px">{{ dialogOptions.icon }}</v-icon>{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <div v-if="dialogOptions.text.length > 0" class="body-1">{{ dialogOptions.text }}</div>
                <v-form ref="dialogForm" style="margin-top:15px; margin-bottom:15px">
                  <div v-if="Object.keys(dialogOptions.item).length > 0">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                    <v-select v-model="dialogOptions.item.time" :items="['Before','After']" :rules="[v => !!v || '']" label="Action Time" auto-select-first required style="padding-top:0px;"></v-select>
                    <v-select v-model="dialogOptions.item.event" :items="['Insert','Update','Delete']" :rules="[v => !!v || '']" label="Event" auto-select-first required style="padding-top:0px;"></v-select>
                    <div style="margin-left:auto; margin-right:auto; height:40vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="dialogSubmit" color="#00b16a">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogOptions.cancel.length > 0">
                      <v-btn :loading="loading2" @click="dialogCancel" color="#EF5354">{{ dialogOptions.cancel }}</v-btn>
                    </v-col>
                    <v-col v-if="loading" cols="auto" class="flex-grow-0 flex-shrink-0">
                      <v-progress-circular indeterminate color="white" size="15" width="1.5" style="height:100%"></v-progress-circular>
                    </v-col>
                    <v-col v-if="loading" cols="auto" class="flex-grow-0 flex-shrink-0" style="padding-left:10px">
                      <div class="body-2" style="height:100%; display:flex; align-items:center">{{ loadingText }}</div>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import ace from 'ace-builds';

import { AgGridVue } from "ag-grid-vue";

import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      loading2: false,
      loadingText: 'Applying changes...',
      // Dialog
      dialog: false,
      dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },
      dialogEditor: null,
      // AG Grid
      selectedRows: false,
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'settings',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'structureHeaders',
      'structureItems',
      'sidebarSelected',
      'bottomBar',
      'headerTabSelected',
      'tabStructureSelected',
    ], { path: 'client/connection' }),
    ...mapFields([
      'gridApi',
      'columnApi',
    ], { path: 'client/components' }),
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (!val) return
      if (this.dialogEditor == null) this.initEditor()
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
    headerTabSelected(val) {
      if (val == 'structure') {
        this.$nextTick(() => {
          if (this.gridApi.structure.triggers != null) this.resizeTable()
        })
      }
    },
    tabStructureSelected(val) {
      if (val == 'triggers') {
        this.$nextTick(() => { this.resizeTable() })
      }
    },
    "structureItems.triggers" () {
      this.selectedRows = false
    }
  },
  methods: {
    initEditor() {
      this.$nextTick(() => {
        // Editor Settings
        this.dialogEditor = ace.edit("dialogEditor", {
          mode: "ace/mode/mysql",
          theme: "ace/theme/monokai",
          keyboardHandler: "ace/keyboard/vscode",
          fontSize: parseInt(this.settings['font_size']) || 14,
          showPrintMargin: false,
          wrap: true,
          autoScrollEditorIntoView: true,
          enableBasicAutocompletion: true,
          enableLiveAutocompletion: true,
          enableSnippets: false,
          highlightActiveLine: false
        });
        this.dialogEditor.session.setOptions({ tabSize: 4, useSoftTabs: false })

        // Add custom keybinds
        this.dialogEditor.commands.removeCommand('showSettingsMenu')
        this.dialogEditor.container.addEventListener("keydown", (e) => {
          // - Increase Font Size -
          if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            let size = parseInt(this.dialogEditor.getFontSize(), 10) || 12
            this.dialogEditor.setFontSize(size + 1)
          }
          // - Decrease Font Size -
          else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            let size = parseInt(this.dialogEditor.getFontSize(), 10) || 12
            this.dialogEditor.setFontSize(Math.max(size - 1 || 1))
          }
        }, false);
      })
    },
    onGridReady(params) {
      this.gridApi.structure.triggers = params.api
      this.columnApi.structure.triggers = params.columnApi
      this.$refs['agGridStructureTriggers'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.structure.triggers.showLoadingOverlay()
    },
    onNewColumnsLoaded() {
      if (this.gridApi.structure.triggers != null) this.resizeTable()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.structure.triggers.deselectAll()
        this.selectedRows = false
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.structure.triggers.getColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.structure.triggers.autoSizeColumns(allColumnIds);
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        let selectedRows = this.gridApi.structure.triggers.getSelectedRows()
        if (selectedRows.length > 1) {
          // Copy values
          let header = Object.keys(selectedRows[0])
          let value = selectedRows.map(row => header.map(fieldName => row[fieldName] == null ? 'NULL' : row[fieldName]).join('\t')).join('\n')
          this.copyToClipboard(value)
          // Apply effect
          // this.gridApi.structure.triggers.flashCells({
          //   rowNodes: this.gridApi.structure.triggers.getSelectedNodes(),
          //   flashDelay: 200,
          //   fadeDelay: 200,
          // })
        }
        else {
          // Copy value
          this.copyToClipboard(e.value).then(() => {
            // Apply effect
            this.gridApi.structure.triggers.flashCells({
              rowNodes: this.gridApi.structure.triggers.getSelectedNodes(),
              columns: [this.gridApi.structure.triggers.getFocusedCell().column.colId],
              flashDelay: 200,
              fadeDelay: 200,
            })
          })
        }
      }
      else if (['ArrowUp','ArrowDown'].includes(e.event.key)) {
        let cell = this.gridApi.structure.triggers.getFocusedCell()
        let row = this.gridApi.structure.triggers.getDisplayedRowAtIndex(cell.rowIndex)
        let node = this.gridApi.structure.triggers.getRowNode(row.id)
        this.gridApi.structure.triggers.deselectAll()
        node.setSelected(true)
      }
    },
    onCellClicked() {
      this.selectedRows = this.gridApi.structure.triggers.getSelectedRows().length != 0
    },
    addTrigger() {
      this.dialogOptions = {
        mode: 'new',
        icon: 'fas fa-plus',
        title: 'NEW TRIGGER',
        text: '',
        item: { name: '', time: '', event: '' },
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialog = true
    },
    removeTrigger() {
      this.dialogOptions = {
        mode: 'delete',
        icon: 'fas fa-minus',
        title: 'DELETE TRIGGER',
        text: "Are you sure you want to delete the trigger '" + this.gridApi.structure.triggers.getSelectedRows()[0].Name + "' from this table? This action cannot be undone.",
        item: {},
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialog = true
    },
    refreshTriggers() {
      EventBus.$emit('get-structure', true)
    },
    dialogSubmit() {
      this.loadingText = 'Applying changes...'
      this.loading = true
      let query = ''
      if (this.dialogOptions.mode == 'new') {
        // Check if all fields are filled
        if (!this.$refs.dialogForm.validate()) {
          EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
          this.loading = false
          return
        }
        // Build query
        let triggerCode = this.dialogEditor.getValue().endsWith(';') ? this.dialogEditor.getValue() : this.dialogEditor.getValue() + ';'
        query = "CREATE TRIGGER `" + this.dialogOptions.item.name.replaceAll('`','``') + '` ' + this.dialogOptions.item.time + ' ' + this.dialogOptions.item.event + ' ON `' + this.sidebarSelected[0]['name'] + '` FOR EACH ROW BEGIN\n' + triggerCode + '\nEND;'
      }
      else if (this.dialogOptions.mode == 'delete') {
        let row = this.gridApi.structure.triggers.getSelectedRows()[0]
        query = "DROP TRIGGER `" + row.Name.replaceAll('`','``') + "`;"
      }
      // Execute query
      this.execute(query)
    },
    execute(query) {
      let promise = new Promise((resolve, reject) => {
        EventBus.$emit('execute-structure', query, false, resolve, reject)
      })
      promise.then(() => { this.dialog = false })
        .catch(() => { if (this.dialogOptions.mode == 'delete') this.dialog = false })
        .finally(() => { this.loading = false })
    },
    dialogCancel() {
      if (this.loading) {
        this.loadingText = 'Interrupting changes...'
        this.loading2 = true
        new Promise((resolve, reject) => {
          EventBus.$emit('stop-structure', resolve, reject)
        }).finally(() => { 
          this.loading2 = false
          this.dialog = false
        })
      }
      else this.dialog = false
    },
    copyToClipboard(textToCopy) {
      if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(textToCopy)
      else {
        let textArea = document.createElement("textarea")
        textArea.value = textToCopy
        textArea.style.position = "absolute"
        textArea.style.opacity = 0
        document.body.appendChild(textArea)
        textArea.select()
        return new Promise((res, rej) => {
          document.execCommand('copy') ? res() : rej()
          textArea.remove()
        })
      }
    },
  }
}
</script>