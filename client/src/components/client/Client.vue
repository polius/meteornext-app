<template>
  <v-main>
    <Header/>
    <v-container fluid>
      <v-main style="padding-top:0px; padding-bottom:0px;">
        <div style="margin: -12px;">
          <div ref="masterDiv" style="height: calc(100vh - 112px);">
            <Connections/>
            <Splitpanes :style="Object.keys(server).length != 0 ? 'height:calc(100% - 49px)' : 'height:100%'">
              <Pane size="20" min-size="0">
                <Sidebar/>
              </Pane>
              <Pane size="80" min-size="0">
                <div style="height:100%; width:100%">
                  <Main/>
                </div>
              </Pane>
            </Splitpanes>
          </div>
        </div>
      </v-main>
    </v-container>
    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </v-main>
</template>

<style scoped>
@import "../../../node_modules/ag-grid-community/dist/styles/ag-grid.css";
@import "../../../node_modules/ag-grid-community/dist/styles/ag-theme-alpine-dark.css";

/* SPLITPANES */
::v-deep .splitpanes__pane {
  box-shadow: 0 0 3px rgba(0, 0, 0, .2) inset;
  justify-content: center;
  align-items: center;
  display: flex;
  position: relative;
}
::v-deep .splitpanes--vertical > .splitpanes__splitter {
  min-width: 2px;
}
::v-deep .splitpanes--horizontal > .splitpanes__splitter {
  min-height: 2px;
}
::v-deep .splitpanes__splitter {background-color:rgba(32, 32, 32, 0.2); position: relative; }
::v-deep .splitpanes__splitter:before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  transition: opacity 0.4s;
  background-color: rgba(32, 32, 32, 0.3);
  opacity: 0;
  z-index: 10;
}
::v-deep .splitpanes__splitter:hover:before  {opacity:1; }
::v-deep .splitpanes--vertical > .splitpanes__splitter:before { left:-3px; right:-3px; height:100%; }
::v-deep .splitpanes--horizontal > .splitpanes__splitter:before { top:-5px; bottom:-3px; width:100%; }

/* ACE EDITOR */
::v-deep .ace_editor {
  margin: auto;
  height: 100%;
  width: 100%;
  background: #272822;
}
::v-deep .ace_content {
  width: 100%;
  height: 100%;
}

/* TREEVIEW */
::v-deep .v-treeview-node__root {
  min-height:30px;
}
::v-deep .v-treeview-node__toggle {
  width: 15px;
}
::v-deep .v-treeview-node__level {
  width: 10px;
}

/* DATA TABLE */
::v-deep .theme--dark.v-data-table.v-data-table--fixed-header thead th {
  background-color: #252525;
}

/* LABEL */
::v-deep .v-label{
  font-size: 0.9rem;
}

/* INPUT */
::v-deep .v-input {
  font-size: 0.9rem;
}

/* APPLICATION */
::v-deep .v-application .elevation-2 {
  box-shadow:none!important;
}

/* CONTAINER */
::v-deep .container {
  padding-bottom:0px;
}
::v-deep .v-text-field .v-input__control .v-input__slot {
  min-height: auto !important;
  display: flex !important;
  align-items: center !important;
}
::v-deep *
{
  will-change: auto !important;
}
::v-deep .ace_editor.ace_autocomplete {
  width: 512px;
}
/* AG GRID */
::v-deep .ag-theme-alpine-dark .ag-header-row {
  font-size: 13px;
  font-weight: 500;
}
::v-deep .ag-theme-alpine-dark .ag-cell {
  font-size: 13px;
  line-height: 30px;
}
::v-deep .ag-theme-alpine-dark .ag-cell-inline-editing {
  height: 30px;
}
::v-deep .ag-theme-alpine-dark {
  --ag-foreground-color:#dcdcdc;
  --ag-header-background-color:#272727;
  --ag-background-color:#2c2c2c;
  --ag-odd-row-background-color:#303030;
  --ag-border-color:#424242;
}
::v-deep .ag-cell-normal {
  color: #dcdcdc;
}
::v-deep .ag-cell-null {
  color: gray;
}
::v-deep tr:hover {
  background-color: transparent !important;
}
</style>

<script>
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import Header from './components/Header'
import Connections from './components/Connections'
import Sidebar from './components/Sidebar'
import Main from './components/Main'

import EventBus from './js/event-bus'

export default {
  data() {
    return {
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(5000),
      snackbarColor: '',
      snackbarText: '',
    }
  },
  components: { Splitpanes, Pane, Header, Connections, Sidebar, Main },
  computed: {
    server () { return this.$store.getters['client/connection'].server },
  },
  mounted () {
    EventBus.$on('SEND_NOTIFICATION', this.notification);
  },
  methods: {
    notification(message, color, timeout=5) {
      this.snackbarText = message
      this.snackbarColor = color
      this.snackbarTimeout = Number(timeout*1000)
      this.snackbar = true
    }
  },
}
</script>