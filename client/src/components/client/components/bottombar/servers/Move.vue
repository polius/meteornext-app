<template>
  <div>
    <!----------------->
    <!-- MOVE SERVER -->
    <!----------------->
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:4px">fas fa-level-up-alt</v-icon>MOVE SERVERS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" @submit.prevent style="margin-top:15px; margin-bottom:15px;">
                  <v-autocomplete ref="focus" @keyup.enter="moveServerSubmit" :disabled="outside" v-model="folder" :items="folders" label="Folder" :rules="[v => !!v || '']" hide-details style="padding-top:0px"></v-autocomplete>
                  <v-switch v-model="outside" flat label="Move out of folders" style="margin-top:15px" hide-details></v-switch>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="moveServerSubmit" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" color="error">Cancel</v-btn>
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
      outside : false,
      folders: [],
      folder: '',
    }
  },
  computed: {
    ...mapFields([
      'servers',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'sidebarSelected',
      'sidebarOpened',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-bottombar-servers-move', this.moveServer)
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (val) {
        this.newName = ''
        requestAnimationFrame(() => {
          if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
          if (typeof this.$refs.focus !== 'undefined') this.$refs.focus.focus()
        })
      }
    }
  },
  methods: {
    moveServer() {
      this.dialog = true
      this.folders = this.servers.filter(x => 'children' in x).map(x => x.name)
      this.folder = ''
      this.outside = false
    },
    moveServerSubmit() {
      // Check if all fields are filled
      if (!this.outside && !this.$refs.form.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', 'error')
        return
      }
      this.loading = true
      let folder = this.servers.find(x => 'children' in x && x.name == this.folder)
      const payload = { 
        servers: {
          servers: this.sidebarSelected.map(x => x.id),
          folder: (folder === undefined || this.outside) ? null : folder.id.substring(1)
        }
      }
      axios.put('/client/servers', payload)
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a', 2)
          this.parseOpenedFolders(payload.servers.folder)
          new Promise((resolve, reject) => EventBus.$emit('get-sidebar-servers', resolve, reject))
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    parseOpenedFolders(folder) {
      if (folder == null) this.sidebarOpened = []
      else this.sidebarOpened = [this.servers.find(x => x.id == 'f' + folder)]
    }
  }
}
</script>