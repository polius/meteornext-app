<template>
  <div>
    <v-dialog v-model="dialog" max-width="80%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text"><v-icon small style="padding-right:10px; padding-bottom:5px">fas fa-shield-alt</v-icon>User Rights</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <!-- <v-btn :disabled="selected.length != 1 || saveButtonDisabled" :loading="loading" @click="editSaved" color="primary" style="margin-right:10px;">Save</v-btn> -->
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <Splitpanes @ready="onSplitPaneReady" style="height:80vh">
                  <Pane size="20" min-size="0" style="align-items:inherit">
                    <v-container fluid style="padding:0px;">
                      <v-row ref="list" no-gutters style="height:calc(100% - 36px); overflow:auto;">
                        <v-treeview :active.sync="rights" item-key="id" :open.sync="rightsOpened" :items="rightsItems" :search="rightsSearch" activatable open-on-click transition class="clear_shadow" style="height:calc(100% - 62px); width:100%; overflow-y:auto;">
                          <template v-slot:label="{item}">
                            <v-btn text style="font-size:14px; text-transform:none; font-weight:400; width:100%; justify-content:left; padding-left:10px;"> 
                              <v-icon v-if="'children' in item" small style="padding-right:10px">fas fa-user</v-icon>
                              {{ item.name }}
                            </v-btn>
                          </template>
                        </v-treeview>
                        <v-text-field v-if="rightsItems.length > 0" v-model="rightsSearch" label="Search" dense solo hide-details height="38px" style="float:left; width:100%; padding:10px;"></v-text-field>
                      </v-row>
                      <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
                        <v-btn text small title="New User Right" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
                        <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                        <v-btn text small title="Delete User Right" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
                        <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                        <v-btn text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
                        <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                      </v-row>
                    </v-container>
                  </Pane>
                  <Pane size="80" min-size="0" style="background-color:#484848">
                   
                  </Pane>
                </Splitpanes>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!------------------>
    <!-- DIALOG: info -->
    <!------------------>
    <v-dialog v-model="infoDialog" persistent max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">An error occurred</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div class="body-2" style="font-weight:300; font-size:1.05rem!important; margin-top:12px;">{{ infoDialogText }}</div>
                  <v-card style="margin-top:20px;">
                    <v-card-text style="padding:10px;">
                      <div class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ infoDialogError }}</div>
                    </v-card-text>
                  </v-card>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="infoDialog = false" color="primary">Close</v-btn>
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
<style scoped src="@/styles/treeview.css"></style>

<script>
import axios from 'axios'

import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

export default {
  data() {
    return {
      dialog: false,
      // Rights
      rights: [],
      rightsSelected: {},
      rightsOpened: [],
      rightsSearch: '',
      // Info Dialog
      infoDialog: false,
      infoDialogText: '',
      infoDialogError: '',
    }
  },
  components: { Splitpanes, Pane },
  computed: {
    ...mapFields([
      'index',
      'server',
      'headerTab',
      'headerTabSelected',
      'rightsItems',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('SHOW_RIGHTS', this.showDialog);
  },
  watch: {
    dialog: function(value) {
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
      }
    }
  },
  methods: {
    showDialog() {
      this.dialog = true
      if (this.rightsItems.length == 0) this.getRights()
    },
    onSplitPaneReady() {
    },
    getRights() {
      const payload = {
        connection: this.index,
        server: this.server.id
      }
      axios.get('/client/rights', { params: payload })
        .then((response) => {
          this.parseRights(response.data.rights)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            // Show Dialog
            this.infoDialogText = 'Cannot retrieve the user permissions. Please check if the current user has SELECT privileges on the mysql.user table.'
            this.infoDialogError = error.response.data.message
            this.infoDialog = true
          }
        })
        .finally(() => {  })
    },
    parseRights(data) {
      var rights = []
      for (let right of data) {
        let index = rights.findIndex(k => k['name'] == right['user'])
        if (index == -1) rights.push({ id: right['user'], name: right['user'], children: [{ id: right['host'], name: right['host'] }] })
        else rights[index]['children'].push({ id: right['host'], name: right['host'] })
      }
      this.rightsItems = rights.slice(0)
    },
  }
}
</script>