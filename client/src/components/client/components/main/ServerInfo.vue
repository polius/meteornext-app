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
            <v-card-text style="padding:15px 15px 20px 15px; margin-bottom:20px">
              <v-row no-gutters>
                <v-col cols="6" style="padding-right:10px">
                  <v-text-field v-model="item.name" readonly label="Name" required style="margin-top:0px; font-size:1rem;" hide-details></v-text-field>
                </v-col>
                <v-col cols="6" style="padding-left:10px">
                  <v-text-field v-model="item.region" readonly label="Region" required style="margin-top:0px; font-size:1rem;" hide-details>
                    <template v-slot:prepend-inner>
                      <v-icon small :title="item.region_shared ? item.region_secured ? 'Shared (Secured)' : 'Shared' : item.region_secured ? 'Personal (Secured)' : 'Personal'" :color="item.region_shared ? '#EB5F5D' : 'warning'" :style="`margin-top:4px; ${!item.region_secured ? 'padding-right:6px' : ''}`">{{ item.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                      <v-icon v-if="item.region_secured" :title="item.region_shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.region_shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-top:7px; padding-left:2px; padding-right:6px">fas fa-lock</v-icon>
                    </template>
                  </v-text-field>
                </v-col>
              </v-row>
              <v-row no-gutters style="margin-top:20px">
                <v-col cols="8" style="padding-right:10px">
                  <v-text-field v-model="item.engine" readonly label="Engine" required style="padding-top:0px; font-size:1rem;" hide-details></v-text-field>
                </v-col>
                <v-col cols="4" style="padding-left:10px">
                  <v-text-field v-model="item.version" readonly label="Version" required style="padding-top:0px; font-size:1rem;" hide-details></v-text-field>
                </v-col>
              </v-row>
              <!-- SQL -->
              <div v-if="!item.secured" style="margin-top:20px">
                <v-row no-gutters>
                  <v-col cols="8" style="padding-right:10px">
                    <v-text-field v-model="item.hostname" readonly label="Hostname" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                  </v-col>
                  <v-col cols="4" style="padding-left:10px">
                    <v-text-field v-model="item.port" readonly label="Port" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                  </v-col>
                </v-row>
                <v-text-field v-model="item.username" readonly label="Username" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                <v-text-field v-model="item.password" readonly label="Password" :append-icon="sqlPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="sqlPassword ? 'text' : 'password'" @click:append="sqlPassword = !sqlPassword" style="padding-top:0px; font-size:1rem;" hide-details></v-text-field>
              </div>
              <!-- SSL -->
              <v-card v-if="item.ssl" style="height:52px; margin-top:15px">
                <v-row no-gutters>
                  <v-col cols="auto" style="display:flex; margin:15px">
                    <v-icon color="#00b16a" style="font-size:16px; margin-top:3px">fas fa-key</v-icon>
                  </v-col>
                  <v-col>
                    <div class="text-body-1" style="color:#00b16a; margin-top:15px">Using a SSL connection</div>
                  </v-col>
                </v-row>
              </v-card>
              <!-- SSH -->
              <v-card v-if="item.ssh" style="height:52px; margin-top:15px">
                <v-row no-gutters>
                  <v-col cols="auto" style="display:flex; margin:15px">
                    <v-icon color="#2196f3" style="font-size:16px; margin-top:4px">fas fa-terminal</v-icon>
                  </v-col>
                  <v-col>
                    <div class="text-body-1" style="color:#2196f3; margin-top:15px">Using a SSH connection</div>
                  </v-col>
                </v-row>
              </v-card>
              <!-- SECURED -->
              <v-card v-if="item.secured" style="height:52px; margin-top:15px">
                <v-row no-gutters>
                  <v-col cols="auto" style="display:flex; margin:15px">
                    <v-icon color="#EF5354" style="font-size:16px; margin-top:4px">fas fa-lock</v-icon>
                  </v-col>
                  <v-col>
                    <div class="text-body-1" style="color:#EF5354; margin-top:15px">This server is secured</div>
                  </v-col>
                </v-row>
              </v-card>
            </v-card-text>
          </v-card>
        </v-flex>
      </v-layout>
    </v-container>
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
    }
  },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'sidebarSelected'
    ], { path: 'client/connection' }),
    item: function() {
      if (this.sidebarSelected.length == 0 || 'children' in this.sidebarSelected[this.sidebarSelected.length - 1]) return []
      else return this.sidebarSelected[this.sidebarSelected.length - 1]
    },
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
}
</script>