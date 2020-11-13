<template>
  <div>
    <!---------------->
    <!-- NEW FOLDER -->
    <!---------------->
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">New Folder</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" @submit.prevent style="margin-top:10px; margin-bottom:15px;">
                  <v-text-field @keyup.enter="newFolderSubmit" v-model="name" :rules="[v => !!v || '']" label="Folder Name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="newFolderSubmit" color="primary">Submit</v-btn>
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

<script>
import axios from 'axios'
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      name: '',
    }
  },
  computed: {
    ...mapFields([
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-bottombar-servers-new-folder', this.newFolder)
  },
  methods: {
    newFolder() {
      this.dialog = true
    },
    newFolderSubmit() {
      const payload = { 'folder': this.name }
      
    },
  }
}
</script>