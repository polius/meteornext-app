<template>
  <div>
    <!-------------------->
    <!-- NEW CONNECTION -->
    <!-------------------->
    <v-dialog v-model="dialog" persistent max-width="70%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">New Connection</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:10px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:5px; margin-bottom:15px;">
                  <div class="body-1" style="margin-left:3px;">Select servers from the <router-link class="nav-link" to="/inventory/servers" target="_blank">inventory</router-link> to add.</div>
                  <v-card style="margin-top:15px">
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="white--text">SERVERS</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-card-text style="padding:0px;">
                      <Splitpanes @ready="onSplitPaneReady" style="height:58vh">
                        <Pane size="40" min-size="0" style="align-items:inherit">
                          <v-container fluid style="padding:0px;">
                            <v-row ref="list" no-gutters style="height:calc(100% - 36px); overflow:auto;">
                              <!-- <v-list style="width:100%; padding:0px;">
                                <v-list-item-group v-model="selected" mandatory multiple>
                                  <v-list-item v-for="(item, i) in items" :key="i" dense :ref="'saved' + i" @click="onListClick($event, i)" @contextmenu="onListRightClick">
                                    <v-list-item-content><v-list-item-title v-text="item.name"></v-list-item-title></v-list-item-content>
                                  </v-list-item>
                                </v-list-item-group>
                              </v-list> -->
                            </v-row>
                            <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
                              <v-btn @click="refresh" text small title="Refresh Servers" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
                              <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                              <v-btn @click="selectAll" text small title="Select All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-check-square</v-icon></v-btn>
                              <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                              <v-btn @click="deselectAll" text small title="Deselect All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">far fa-square</v-icon></v-btn>
                              <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                            </v-row>
                          </v-container>
                        </Pane>
                        <Pane size="80" min-size="0" style="background-color:#484848">
                        </Pane>
                      </Splitpanes>
                    </v-card-text>
                  </v-card>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="newConnectionSubmit" color="primary">Save</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">Cancel</v-btn>
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

<style scoped src="@/styles/splitPanes.css"></style>

<script>
import axios from 'axios'
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      search: '',
      items: [],
    }
  },
  components: { Splitpanes, Pane },
  computed: {
    ...mapFields([
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-bottombar-connections-new', this.newConnection)
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
      })
    },
  },
  methods: {
    onSplitPaneReady() {

    },
    getServers() {
      axios.get('/inventory/servers')
        .then((response) => {
          this.items = response.data.data
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    newConnection() {
      this.dialog = true
    },
    newConnectionSubmit() {
      this.dialog = false
    },
    refresh() {

    },
    selectAll() {

    },
    deselectAll() {

    },
  }
}
</script>