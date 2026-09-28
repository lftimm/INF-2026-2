;; https://guix.bordeaux.inria.fr/eval/9004109
;; 2025-10-09 11:51:42

(list (channel
        (name 'guix-hpc-non-free)
        (url "https://gitlab.inria.fr/guix-hpc/guix-hpc-non-free.git")
        (branch "master")
        (commit
          "8c4260a216e9b4a4d9647ecaaef4341308273761"))
      (channel
        (name 'guix)
        (url "https://git.guix.gnu.org/guix.git")
        (branch "master")
        (commit
          "925d10cc642d60c3f67a8423b4636da3c618e983")
        (introduction
          (make-channel-introduction
            "9edb3f66fd807b096b48283debdcddccfea34bad"
            (openpgp-fingerprint
              "BBB0 2DDF 2CEA F6A8 0D1D  E643 A2A0 6DF2 A33A 54FA"))))
      (channel
        (name 'guix-hpc)
        (url "https://gitlab.inria.fr/guix-hpc/guix-hpc.git")
        (branch "master")
        (commit
          "32c313f2262c529bec26543d63e3e931b2d18385"))
      (channel
        (name 'guix-science-nonfree)
        (url "https://codeberg.org/guix-science/guix-science-nonfree.git")
        (branch "master")
        (commit
          "baee36c468c8b23cff98ae90d6598291547b869f")
        (introduction
          (make-channel-introduction
            "58661b110325fd5d9b40e6f0177cc486a615817e"
            (openpgp-fingerprint
              "CA4F 8CF4 37D7 478F DA05  5FD4 4213 7701 1A37 8446"))))
      (channel
        (name 'guix-science)
        (url "https://codeberg.org/guix-science/guix-science.git")
        (branch "master")
        (commit
          "d724d9ecedb4507bf157682b30914ac0fa99d025")
        (introduction
          (make-channel-introduction
            "b1fe5aaff3ab48e798a4cce02f0212bc91f423dc"
            (openpgp-fingerprint
              "CA4F 8CF4 37D7 478F DA05  5FD4 4213 7701 1A37 8446"))))
      (channel
        (name 'guix-past)
        (url "https://codeberg.org/guix-science/guix-past.git")
        (branch "master")
        (commit
          "c3bc94ee752ec545e39c1b8a29f739405767b51c")
        (introduction
          (make-channel-introduction
            "0c119db2ea86a389769f4d2b9c6f5c41c027e336"
            (openpgp-fingerprint
              "3CE4 6455 8A84 FDC6 9DB4  0CFB 090B 1199 3D9A EBB5")))))

