<template>
  <div>
    <!------------------->
    <!-- RENAME FOLDER -->
    <!------------------->
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:2px">fas fa-feather-alt</v-icon>RENAME FOLDER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:15px">
                  <v-text-field readonly v-model="currentName" :rules="[v => !!v || '']" label="Current name" required style="padding-top:0px;"></v-text-field>
                  <v-text-field @keyup.enter="renameFolderSubmit" v-model="newName" :rules="[v => !!v || '']" label="New name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="renameFolderSubmit" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn :disabled="loading" @click="dialog = false" color="#EF5354">Cancel</v-btn>
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
      currentName: '',
      newName: '',
    }
  },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('show-bottombar-servers-rename-folder', this.renameFolder)
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (val) {
        this.newName = ''
        requestAnimationFrame(() => {
          if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        })
      }
    }
  },
  methods: {
    renameFolder() {
      this.dialog = true
      this.currentName = this.sidebarSelected[0].name
    },
    renameFolderSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      this.loading = true
      const payload = { folder: { id: this.sidebarSelected[0].id.substring(1), name: this.newName }}
      axios.put('/client/servers', payload)
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a', 2)
          new Promise((resolve, reject) => EventBus.$emit('get-sidebar-servers', resolve, reject))
          .then(() => this.sidebarSelected[0]['name'] = this.newName)
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
  }
}
</script>