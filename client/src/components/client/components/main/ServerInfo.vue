<template>
  <div style="height:100%; overflow-y:auto;">
    <!----------------->
    <!-- SERVER INFO -->
    <!----------------->
    <v-container :style="`height:max(${height},100%); width:70%; display:flex; align-items:center; justify-content:center;`">
      <v-layout wrap>
        <v-flex v-show="item.length == 0" xs12>
          <div class="body-2" style="margin-top:1%; text-align:center;">Select a server to show the details</div>
        </v-flex>
        <v-flex ref="item" v-show="item.length != 0">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Server details</div>
          <v-card>
            <v-card-text style="padding:23px 20px 5px 20px; margin-bottom:20px;">
              <v-row no-gutters>
                <v-col cols="8" style="padding-right:10px">
                  <v-text-field v-model="item.name" readonly label="Name" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
                <v-col cols="4" style="padding-left:10px">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:8px">
                      <v-icon small :title="item.region_shared ? 'Shared' : 'Personal'" :color="item.region_shared ? 'error' : 'warning'" style="margin-top:13px">{{ item.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                    </v-col>
                    <v-col>
                      <v-text-field v-model="item.region" readonly label="Region" r equired style="padding-top:0px; font-size:1rem;"></v-text-field>
                    </v-col>
                  </v-row>
                </v-col>
              </v-row>
              <!-- SQL -->
              <v-row no-gutters>
                <v-col cols="8" style="padding-right:10px">
                  <v-text-field v-model="item.engine" readonly label="Engine" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
                <v-col cols="4" style="padding-left:10px">
                  <v-text-field v-model="item.version" readonly label="Version" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
              </v-row>
              <div v-if="!(inventory_secured && !owner && item.shared)">
                <v-row no-gutters style="margin-top:10px;">
                  <v-col cols="8" style="padding-right:10px">
                    <v-text-field v-model="item.hostname" readonly label="MySQL Hostname" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                  </v-col>
                  <v-col cols="4" style="padding-left:10px">
                    <v-text-field v-model="item.port" readonly label="Port" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                  </v-col>
                </v-row>
                <v-text-field v-model="item.username" readonly label="Username" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                <v-text-field v-model="item.password" readonly label="Password" :append-icon="sqlPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="sqlPassword ? 'text' : 'password'" @click:append="sqlPassword = !sqlPassword" style="padding-top:0px; font-size:1rem;"></v-text-field>
                <!-- SSH -->
                <div v-if="item.ssh_enabled">
                  <v-row no-gutters style="margin-top:15px;">
                    <v-col cols="8" style="padding-right:10px">
                      <v-text-field v-model="item.ssh_hostname" readonly label="SSH Hostname" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-text-field v-model="item.ssh_port" readonly label="Port" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                    </v-col>
                  </v-row>
                  <v-text-field v-model="item.ssh_username" readonly label="Username" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                  <v-row no-gutters>
                    <v-col style="padding-right:10px">
                      <v-text-field v-model="item.ssh_password" readonly label="Password" :append-icon="sshPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="sshPassword ? 'text' : 'password'" @click:append="sshPassword = !sshPassword" style="padding-top:0px; font-size:1rem;"></v-text-field>
                    </v-col>
                    <v-col cols="auto" style="padding-left:10px">
                      <v-btn @click="sshClick" color="#2e3131">SSH Key</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-flex>
      </v-layout>
    </v-container>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">{{ dialogTitle }}</div>
              <v-flex xs12>
                <div style="max-height:70vh; padding:15px 10px 0px 5px; overflow-y:auto;">
                  <v-textarea readonly solo counter auto-grow :value="dialogText"></v-textarea>
                </div>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="dialog = false" color="primary">Close</v-btn>
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
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      height: '100%',
      sqlPassword: false,
      sshPassword: false,
      // Dialog
      dialog: false,
      dialogTitle: '',
      dialogText: '',
    }
  },
  computed: {
    ...mapFields([
      'sidebarSelected'
    ], { path: 'client/connection' }),
    item: function() {
      if (this.sidebarSelected.length == 0) return []
      else return this.sidebarSelected[this.sidebarSelected.length - 1]
    },
    owner: function() { return this.$store.getters['app/owner'] == 1 ? true : false },
    inventory_secured: function() { return this.$store.getters['app/inventory_secured'] },
  },
  watch: {
    sidebarSelected (val) {
      if (val) {
        this.$nextTick(() => {
          if (this.$refs.item !== undefined && this.$refs.item.clientHeight != 0) {
            this.height = this.$refs.item.clientHeight + 25 + 'px'
          }
        })
      }
    },
  },
  methods: {
    sshClick() {
      this.dialogTitle = 'SSH Key'
      this.dialogText = this.item.ssh_key
      this.dialog = true
    },
  },
}
</script>